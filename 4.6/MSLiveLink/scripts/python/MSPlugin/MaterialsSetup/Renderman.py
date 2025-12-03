
from ..Utilities.SingletonBase import Singleton
from .MaterialsCreator import MaterialsCreator

import os
import platform
import subprocess
import hou

# Albedo -> PxrSurface.diffuseColour
# Bump -> PxrSurface.bumpNormal
# Displacement -> PxrDisplace
# Fuzz -> PxrSurface.fuzzGain
# Normal -> PxrNormalMap
# Roughness -> PxrSurface.specularRoughness
# Specular -> PxrSurface.specularEdgeColour

def convertToTex(inputPath):
    rendermanPath = os.getenv("RMANTREE")
    if platform.system().lower() == "windows":
        texConverter = "txmake.exe"
    elif platform.system().lower() == "darwin":
        texConverter = "txmake"
    elif platform.system().lower() == "linux":
        texConverter = "txmake"

    converterPath = os.path.join(rendermanPath, "bin", texConverter)    
    if not os.path.isfile(converterPath):
        return ""

    try :
        filepath, fileextension = os.path.splitext(inputPath)
        texFile = filepath + ".tex"        
        if os.path.isfile(texFile):
            return texFile
        conversionArgs = converterPath + " " + "-mode periodic" + " " + '"' + inputPath + '"' + " " + '"' + texFile+'"'        
        converting = subprocess.Popen(conversionArgs, stdout=subprocess.PIPE)
        out, err = converting.communicate()
        if err:            
            return ""
        return texFile

    except:
        return ""



class RendermanPixarSurface:
    def __init_(self):
        self.nonLinearMaps = ["albedo", "specular", "translucency"]
    
    def createMaterial(self, assetData, importParams, importOptions):
        rendermanPath = os.getenv("RMANTREE")
        if rendermanPath is None:            
            return None


        self.nonLinearMaps = ["albedo", "specular", "translucency"]

        self.paramMapping ={
            "defaultParams" :{
                "diffuseColorr" : 1,
                "diffuseColorg" : 1,
                "diffuseColorb" : 1,
                "specularFaceColorr" : 1,
                "specularFaceColorg" : 1,
                "specularFaceColorb" : 1,
                "specularEdgeColorr" : 1,
                "specularEdgeColorg" : 1,
                "specularEdgeColorb" : 1,
                "specularRoughness" : 0,
                "specularModelType" : 1,
                "specularFresnelMode" :1
            },
            "mapConnections" : {
                "albedo" : {
                    "input" : "diffuseColor",
                    "output" : "resultRGB"
                },
                "diffuse" : {
                    "input" : "diffuseColor",
                    "output" : "resultRGB"
                },
                "roughness" : {
                    "input" : "specularRoughness",
                    "output" : "resultF"
                },
                "specular" : {
                    "input" : "specularEdgeColor",
                    "output" : "resultRGB"
                },
                "fuzz" :{
                    "input" : "fuzzGain",
                    "output" : "resultR"
                },
                "normal" : {
                    "input" : "bumpNormal",
                    "output" : "resultN"
                },
                "bump" : {
                    "input" : "bumpNormal",
                    "output" : "resultN"
                },
                "displacement" :{
                    "input" : "shader1",
                    "output" : "displace"
                },
                "opacity" : {
                    "input" : "presence",
                    "output" : "resultR"
                }
            }

        } #parameter mapping from texture type, output name and input name
        materialNode = hou.node(importParams["materialPath"]).createNode("pxrsurface::3.0", importParams["assetName"])

        for defaultParam in self.paramMapping["defaultParams"].keys():
            materialNode.parm(defaultParam).set(self.paramMapping["defaultParams"][defaultParam])

        outputNode = materialNode
        if assetData["type"] == "surface" :
            manifoldNode = hou.node(importParams["materialPath"]).createNode("pxrmanifold2d::3.0")

        for textureData in assetData["components"]:
            if textureData["type"] == "metalness":
                materialNode.parm("specularExtinctionCoeffr").set(3)
                materialNode.parm("specularExtinctionCoeffg").set(3)
                materialNode.parm("specularExtinctionCoeffb").set(3)

            if textureData["type"] not in self.paramMapping["mapConnections"].keys(): continue
            textureNode = hou.node(importParams["materialPath"]).createNode("pxrtexture::3.0", assetData["id"] + "_" + textureData["type"])
            if textureData["type"] in self.nonLinearMaps: textureNode.parm("linearize").set(1)
            texFile = convertToTex(textureData["path"])
            texFile = texFile.replace("\\", "/")
            textureNode.parm("filename").set(texFile)
            textureParams = self.paramMapping["mapConnections"][textureData["type"]]
            if textureData["type"] == "normal":                
                normalNode = hou.node(importParams["materialPath"]).createNode("pxrnormalmap::3.0", assetData["id"] + "_pxrNormal")
                normalNode.setNamedInput("inputRGB", textureNode, "resultRGB")
                materialNode.setNamedInput(textureParams["input"], normalNode, textureParams["output"])

            elif textureData["type"] == "bump":
                bumpNode = hou.node(importParams["materialPath"]).createNode("pxrbump::3.0", assetData["id"] + "_pxrBump")
                bumpNode.setNamedInput("inputBump", textureNode, "resultR")
                materialNode.setNamedInput(textureParams["input"], bumpNode, textureParams["output"])

                
            elif textureData["type"] == "displacement":
                collectionNode = hou.node(importParams["materialPath"]).createNode("collect", importParams["assetName"] + "_displacement")
                dispNode = hou.node(importParams["materialPath"]).createNode("pxrdisplace::3.0", assetData["id"]+ "_pxrDisplace")
                # dispNode.setNamedInput("dispAmount", textureNode, "resultR")
                dispTransformNode = hou.node(importParams["materialPath"]).createNode("pxrdisptransform::3.0", assetData["id"]+ "_pxrDispTransform")
                dispTransformNode.setNamedInput("dispScalar", textureNode, "resultR")
                dispNode.setNamedInput("dispScalar", dispTransformNode, "resultF")
                dispTransformNode.parm("dispRemapMode").set(2)

                dispTransformNode.parm("dispHeight").set(0.1)
                dispTransformNode.parm("dispDepth").set(0.1)

                if assetData["type"] == "surface" or assetData["type"] == "atlas":
                    dispValue = "0.15"
                    for assetMeta in assetData["meta"]:
                        if assetMeta["key"] == "height":
                            dispValue = assetMeta["value"].split(" ")[0]
                    dispNode.parm("dispScalar").set(dispValue)
                else : dispNode.parm("dispScalar").set("0.01")

               
                # collectionNode.setNamedInput("shader1", dispNode, "displace")
                # collectionNode.setNamedInput("shader2", materialNode, "bxdf_out")

                collectionNode.setInput(0, dispNode, 0)
                collectionNode.setInput(1, materialNode, 0)

                outputNode = collectionNode

                    
            elif textureData["type"] == "roughness":
                roughnessConverter = hou.node(importParams["materialPath"]).createNode("pxrtofloat::3.0")
                roughnessConverter.setNamedInput("input", textureNode, "resultRGB")
                materialNode.setNamedInput(textureParams["input"], roughnessConverter, textureParams["output"])

            else:
                materialNode.setNamedInput(textureParams["input"], textureNode, textureParams["output"])

            if assetData["type"] == "surface" :          
                
                textureNode.setNamedInput("manifold", manifoldNode, "result")              
                

            


        return outputNode    



class RendermanTriplanarSurface:
    def __init_(self):
        self.nonLinearMaps = ["albedo", "specular", "translucency"]
    
    def createMaterial(self, assetData, importParams, importOptions):
        rendermanPath = os.getenv("RMANTREE")
        if rendermanPath is None:            
            return None


        self.nonLinearMaps = ["albedo", "specular", "translucency"]
        self.paramMapping ={
            "defaultParams" :{
                "diffuseColorr" : 1,
                "diffuseColorg" : 1,
                "diffuseColorb" : 1,
                "specularFaceColorr" : 1,
                "specularFaceColorg" : 1,
                "specularFaceColorb" : 1,
                "specularEdgeColorr" : 1,
                "specularEdgeColorg" : 1,
                "specularEdgeColorb" : 1,
                "specularRoughness" : 0,
                "specularModelType" : 1,
                "specularFresnelMode" :1
            },
            "mapConnections" : {
                "albedo" : {
                    "input" : "diffuseColor",
                    "output" : "resultRGB"
                },
                "diffuse" : {
                    "input" : "diffuseColor",
                    "output" : "resultRGB"
                },
                "roughness" : {
                    "input" : "specularRoughness",
                    "output" : "resultF"
                },
                "specular" : {
                    "input" : "specularEdgeColor",
                    "output" : "resultRGB"
                },
                "fuzz" :{
                    "input" : "fuzzGain",
                    "output" : "resultR"
                },
                "normal" : {
                    "input" : "bumpNormal",
                    "output" : "resultN"
                },
                "bump" : {
                    "input" : "bumpNormal",
                    "output" : "resultN"
                },
                "displacement" :{
                    "input" : "shader1",
                    "output" : "displace"
                },
                "opacity" : {
                    "input" : "presence",
                    "output" : "resultR"
                }
            }

        } #parameter mapping from texture type, output name and input name
        materialNode = hou.node(importParams["materialPath"]).createNode("pxrsurface::3.0", importParams["assetName"])

        for defaultParam in self.paramMapping["defaultParams"].keys():
            materialNode.parm(defaultParam).set(self.paramMapping["defaultParams"][defaultParam])

        outputNode = materialNode
        
        roundCubeNode = hou.node(importParams["materialPath"]).createNode("pxrroundcube::3.0")

        for textureData in assetData["components"]:
            if textureData["type"] == "metalness":
                materialNode.parm("specularExtinctionCoeffr").set(3)
                materialNode.parm("specularExtinctionCoeffg").set(3)
                materialNode.parm("specularExtinctionCoeffb").set(3)

            
            textureNode = hou.node(importParams["materialPath"]).createNode("pxrmultitexture::3.0", assetData["id"] + "_" + textureData["type"])
            if textureData["type"] in self.nonLinearMaps: textureNode.parm("linearize").set(1)
            texFile = convertToTex(textureData["path"])
            texFile = texFile.replace("\\", "/")
            textureNode.parm("filename0").set(texFile)

            if textureData["type"] not in self.paramMapping["mapConnections"].keys(): continue

            textureParams = self.paramMapping["mapConnections"][textureData["type"]]
            if textureData["type"] == "normal":                
                normalNode = hou.node(importParams["materialPath"]).createNode("pxrnormalmap::3.0", assetData["id"] + "_pxrNormal")
                normalNode.setNamedInput("inputRGB", textureNode, "resultRGB")
                materialNode.setNamedInput(textureParams["input"], normalNode, textureParams["output"])

            elif textureData["type"] == "bump":
                bumpNode = hou.node(importParams["materialPath"]).createNode("pxrbump::3.0", assetData["id"] + "_pxrBump")
                bumpNode.setNamedInput("inputBump", textureNode, "resultR")
                materialNode.setNamedInput(textureParams["input"], bumpNode, textureParams["output"])

            elif textureData["type"] == "displacement":
                collectionNode = hou.node(importParams["materialPath"]).createNode("collect", importParams["assetName"] + "_displacement")
                dispNode = hou.node(importParams["materialPath"]).createNode("pxrdisplace::3.0", assetData["id"]+ "_pxrDisplace")
                # dispNode.setNamedInput("dispAmount", textureNode, "resultR")
                dispTransformNode = hou.node(importParams["materialPath"]).createNode("pxrdisptransform::3.0", assetData["id"]+ "_pxrDispTransform")
                dispTransformNode.setNamedInput("dispScalar", textureNode, "resultR")
                dispNode.setNamedInput("dispScalar", dispTransformNode, "resultF")
                dispTransformNode.parm("dispRemapMode").set(2)


                dispTransformNode.parm("dispHeight").set(0.1)
                dispTransformNode.parm("dispDepth").set(0.1)

                if assetData["type"] == "surface" or assetData["type"] == "atlas":
                    dispValue = "0.15"
                    for assetMeta in assetData["meta"]:
                        if assetMeta["key"] == "height":
                            dispValue = assetMeta["value"].split(" ")[0]
                    dispNode.parm("dispScalar").set(dispValue)
                else : dispNode.parm("dispScalar").set("0.01")
               
                # collectionNode.setNamedInput("shader1", dispNode, "displace")
                # collectionNode.setNamedInput("shader2", materialNode, "bxdf_out")

                collectionNode.setInput(0, dispNode, 0)
                collectionNode.setInput(1, materialNode, 0)

                outputNode = collectionNode

                    
            elif textureData["type"] == "roughness":
                roughnessConverter = hou.node(importParams["materialPath"]).createNode("pxrtofloat::3.0")
                roughnessConverter.setNamedInput("input", textureNode, "resultRGB")
                materialNode.setNamedInput(textureParams["input"], roughnessConverter, textureParams["output"])

            else:
                materialNode.setNamedInput(textureParams["input"], textureNode, textureParams["output"])                    
                
            textureNode.setNamedInput("manifoldMulti", roundCubeNode, "resultMulti")              
                

            
        

        return outputNode    



def registerRendermanMaterials():    
    # materialTypes = ["Principled", "Triplanar"]
    pixarSurfaceFactory = RendermanPixarSurface()
    rendermanTriplanar = RendermanTriplanarSurface()

    materialsCreator = MaterialsCreator()
    materialsCreator.registerMaterial("Renderman", "Pixar Surface", pixarSurfaceFactory.createMaterial)
    materialsCreator.registerMaterial("Renderman", "Pixar Triplanar", rendermanTriplanar.createMaterial)
    
    # materialsCreator.registerMaterial("Renderman", "PixarSurface_USD", pixarSurfaceFactory.createMaterial)
    

registerRendermanMaterials()

