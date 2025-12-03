from ..Utilities.SingletonBase import Singleton
from ..MaterialsSetup.MaterialsCreator import MaterialsCreator
from ..MaterialsSetup import *
import hou, os

from six import with_metaclass

class ImportSurface(with_metaclass(Singleton)):

    def __init__(self):
        pass
    
    @staticmethod
    def parm_exist(parmpath):
        nodepath, parmname = os.path.split(parmpath)
        node = hou.node(nodepath)
        if node is None:
            return False
        return node.parmTuple(parmname) != None

    def importAsset(self, assetData, importOptions, importParams):
        
        # asset import parameters
        materialsCreator = MaterialsCreator()
        importedSurface = None

        # defensive defaults for nested options that might be missing
        ui_opts = importOptions.get("UI", {})
        import_opts = ui_opts.get("ImportOptions", {})
        usd_opts = ui_opts.get("USDOptions", {})

        enable_usd = import_opts.get("EnableUSD", False)
        renderer = import_opts.get("Renderer", "")
        material_choice = import_opts.get("Material", "")

        if not enable_usd:
            if renderer == "Karma" :
                pass
            if renderer == "Redshift" :
                # create redshift container (use positional name arg)
                redshiftContainer = hou.node(importParams["materialPath"]).createNode("redshift_vopnet", importParams["assetName"], run_init_scripts=False)
                importParams["materialPath"] = redshiftContainer.path()
                albedoPath = str(hou.node(redshiftContainer.path() + "/albedo"))

                ##############################################

                nodeParams = hou.node(str(redshiftContainer.path()))
                nodeParamsGroups = nodeParams.parmTemplateGroup()
                expA = "`chs(\"albedo/tex0\")`"
                expB = "`chs(\"displacement/tex0\")`"
                expC = "`chs(\"Sprite1/tex0\")`"

                nodeTexParam = hou.FolderParmTemplate(
                    "rstexs",
                    "RS Textures",
                    folder_type=hou.folderType.Simple,
                    parm_templates=[
                        hou.FloatParmTemplate("rs_tex_uvscale1", "Scale", 2, default_expression=("ch(\"albedo/scale1\")", "ch(\"albedo/scale2\")"), default_expression_language=(hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript)),
                        hou.FloatParmTemplate("rs_tex_uvtranslate1", "Offset", 2, default_expression=("ch(\"albedo/offset1\")", "ch(\"albedo/offset2\")"), default_expression_language=(hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript)),
                        hou.FloatParmTemplate("rs_tex_uvrotate1", "Rotate", 1, default_expression=[("ch(\"albedo/rotate\")")], default_expression_language=(hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript)),
                        hou.ToggleParmTemplate("ogl_use_tex1", "Display Texture", default_value=True)
                    ]
                )
                nodeAddParam = hou.FolderParmTemplate(
                    "ogltexs",
                    "OGL Textures",
                    folder_type=hou.folderType.Simple,
                    parm_templates=[
                        hou.StringParmTemplate("ogl_tex1", "Texture", 1, [expA]),
                        hou.StringParmTemplate("ogl_opacitymap", "Alpha", 1, [expC]),
                        hou.FloatParmTemplate("ogl_tex_uvscale1", "Scale", 2, default_expression=("1/ch(\"albedo/scale1\")", "1/ch(\"albedo/scale2\")"), default_expression_language=(hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript)),
                        hou.FloatParmTemplate("ogl_tex_uvtranslate1", "Offset", 2, default_expression=("ch(\"albedo/offset1\")", "ch(\"albedo/offset2\")"), default_expression_language=(hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript)),
                        hou.FloatParmTemplate("ogl_tex_uvrotate1", "Rotate", 1, default_expression=[("ch(\"albedo/rotate\")")], default_expression_language=(hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript))
                    ]
                )

                nodeAddDispParam = hou.FolderParmTemplate(
                    "ogltexs",
                    "OGL Displacement",
                    folder_type=hou.folderType.Simple,
                    parm_templates=[
                        hou.ToggleParmTemplate("ogl_use_displacemap", "Displace", default_value=False),
                        hou.FloatParmTemplate("ogl_displacescale", "Displace Scale", 1, default_expression=[("ch(\"Displacement1/scale\")")], default_expression_language=(hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript)),
                        hou.FloatParmTemplate("ogl_displaceoffset", "Displace Offset", 1, default_expression=[("ch(\"Displacement1/newrange_min\")")], default_expression_language=(hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript)),
                        hou.StringParmTemplate("ogl_displacemap", "Texture", 1, [expB]),
                        hou.FloatParmTemplate("ogl_displace_uvscale", "UV Scale", 2, default_expression=("1/ch(\"displacement/scale1\")", "1/ch(\"displacement/scale2\")"), default_expression_language=(hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript)),
                        hou.FloatParmTemplate("ogl_displace_uvtranslate", "UV Offset", 2, default_expression=("ch(\"displacement/offset1\")", "ch(\"displacement/offset2\")"), default_expression_language=(hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript)),
                        hou.FloatParmTemplate("ogl_displace_uvrotate", "UV Rotate", 1, default_expression=[("ch(\"displacement/rotate\")")], default_expression_language=(hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript))
                    ]
                )

                nodeParamsGroups.append(nodeTexParam)
                nodeParamsGroups.append(nodeAddDispParam)
                nodeParamsGroups.append(nodeAddParam)
                redshiftContainer.setParmTemplateGroup(nodeParamsGroups)

            elif renderer == "Arnold":
                arnoldContainer = hou.node(importParams["materialPath"]).createNode("arnold_materialbuilder", importParams["assetName"], run_init_scripts=False)
                importParams["materialPath"] = arnoldContainer.path()

            elif renderer == "Octane":
                octaneContainer = hou.node(importParams["materialPath"]).createNode("octane_vopnet", importParams["assetName"], run_init_scripts=False)
                importParams["materialPath"] = octaneContainer.path()

            elif renderer == "Renderman":
                rendermanContainer = hou.node(importParams["materialPath"]).createNode("pxrmaterialbuilder", importParams["assetName"], run_init_scripts=False)
                importParams["materialPath"] = rendermanContainer.path()


            importedSurface = materialsCreator.createMaterial(renderer, material_choice, assetData, importParams, importOptions)
            
            hou.node(importParams["materialPath"]).moveToGoodPosition()
            hou.node("/mat").moveToGoodPosition()
            
            if renderer == "Arnold":
                return arnoldContainer

            if renderer == "Octane":
                return octaneContainer

            if renderer == "Redshift":
                return redshiftContainer

            if renderer == "Renderman":
                hou.node(importParams["materialPath"]).layoutChildren()
                return rendermanContainer

            # eğer importedSurface bir node objesi ise seç
            try:
                importedSurface.setSelected(True)
            except Exception:
                pass
            return importedSurface
        
        # EnableUSD && importType == "Normal"
        elif enable_usd and importParams.get("importType", "") == "Normal" :
            usd_renderer = usd_opts.get("USDMaterial", "")
            if renderer == "Redshift" :
                redshiftContainer = hou.node(importParams["materialPath"]).createNode("redshift_vopnet", importParams["assetName"], run_init_scripts=False)
                importParams["materialPath"] = redshiftContainer.path()

            elif renderer == "Arnold":
                arnoldContainer = hou.node(importParams["materialPath"]).createNode("arnold_materialbuilder", importParams["assetName"], run_init_scripts=False)
                importParams["materialPath"] = arnoldContainer.path()

            elif renderer == "Octane":
                octaneContainer = hou.node(importParams["materialPath"]).createNode("octane_vopnet", importParams["assetName"], run_init_scripts=False)
                importParams["materialPath"] = octaneContainer.path()

            elif renderer == "Renderman":
                rendermanContainer = hou.node(importParams["materialPath"]).createNode("pxrmaterialbuilder", importParams["assetName"], run_init_scripts=False)
                importParams["materialPath"] = rendermanContainer.path()


            importedSurface = materialsCreator.createMaterial(renderer, material_choice, assetData, importParams, importOptions)
            
            hou.node(importParams["materialPath"]).moveToGoodPosition()
            hou.node("/mat").moveToGoodPosition()
            
            if renderer == "Arnold":
                return arnoldContainer

            if renderer == "Octane":
                return octaneContainer

            if renderer == "Redshift":
                return redshiftContainer

            if renderer == "Renderman":
                hou.node(importParams["materialPath"]).layoutChildren()
                return rendermanContainer
            
            try:
                importedSurface.setSelected(True)
            except Exception:
                pass
            return importedSurface
            ##########################################
            #
            #      Modified section
            #
            ##########################################
        
        else:
            # USD path
            usdMaterials = {"Karma" : "Karma", "Renderman" : "Pixar Surface", "Arnold" : "Standard Surface", "Redshift_USD" : "Redshift_USD"}
            usdRendererType = usd_opts.get("USDMaterial", "")

            # fix ambiguous conditions with parentheses to be explicit
            if (assetData.get("type") == "surface") or (assetData.get("type") == "atlas" and not import_opts.get("UseAtlasSplitter", False)) or (assetData.get("type") == "brush"):
                usdMaterialContainer = hou.node(importParams["materialPath"]).createNode("materiallibrary", importParams["assetName"])
                importParams["materialPath"] = usdMaterialContainer.path()

            # Adjust Karma/Mantra logic
            if usdRendererType == "Karma":
                usdRendererType = "Mantra"
                if (not import_opts.get("UseAtlasSplitter", False)) or assetData.get("type") == "3d":
                    usdRendererType = "Karma"
                    karmaContainer = hou.node(importParams["materialPath"]).createNode("subnet", importParams["assetName"])
                    importParams["materialPath"] = karmaContainer.path()
            
            if usd_opts.get("USDMaterial", "") == "Redshift_USD":
                importOptions.setdefault("UI", {}).setdefault("USDOptions", {})["Material"] = "Redshift Material"
                importOptions["UI"]["USDOptions"]["Renderer"] = "Redshift"
                redshiftContainer = hou.node(importParams["materialPath"]).createNode("rs_usd_material_builder", importParams["assetName"])
                importParams["materialPath"] = redshiftContainer.path()
    
            if usd_opts.get("USDMaterial", "") == "Arnold":
                arnoldContainer = hou.node(importParams["materialPath"]).createNode("arnold_materialbuilder", importParams["assetName"], run_init_scripts=False)
                importParams["materialPath"] = arnoldContainer.path()
            
            # güvenli erişim: USDmatLoop anahtarı eksikse False kabul et
            usd_mat_loop = import_opts.get("USDmatLoop", False)
            if import_opts.get("USDmatLoop", False) == True and usdRendererType == "Mantra":
                usdRendererType = "Karma"
                karmaContainer = hou.node(importParams["materialPath"]).createNode("subnet", importParams["assetName"])
                importParams["materialPath"] = karmaContainer.path()

            importedSurface = materialsCreator.createMaterial(usdRendererType, usdMaterials.get(usdRendererType, usdMaterials.get("Karma")), assetData, importParams, importOptions)
            if usd_opts.get("USDMaterial", "") == "Arnold" :
                dispValue = "0.008"
                if assetData.get("type") in ("surface", "atlas"):                    
                    for assetMeta in assetData.get("meta", []):
                        if assetMeta.get("key") == "height":
                            dispValue = str(assetMeta.get("value", "")).split(" ")[0]
                
                    renderSettings = usdMaterialContainer.createOutputNode("rendergeometrysettings")
                    # eski kod renderSettings.parm("arnolddisp_height_control")#.set("set")
                    renderSettings.parm("xn__primvarsarnolddisp_height_uhbg").set(dispValue)
                    
                importedSurface = arnoldContainer

            if (assetData.get("type") == "surface") or (assetData.get("type") == "atlas" and not import_opts.get("UseAtlasSplitter", False)) or (assetData.get("type") == "brush"):
                usdMaterialContainer.parm("matnode1").set(importParams["assetName"])
                usdMaterialContainer.parm("matpath1").set(importParams["assetName"])

            hou.node(importParams["materialPath"]).moveToGoodPosition()
            hou.node("/mat").moveToGoodPosition()
            try:
                importedSurface.setSelected(True)
            except Exception:
                pass

            return importedSurface
