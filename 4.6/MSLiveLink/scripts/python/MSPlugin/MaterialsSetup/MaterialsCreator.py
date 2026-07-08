from ..Utilities.SingletonBase import Singleton
from six import with_metaclass

class MaterialsCreator(with_metaclass(Singleton)):
    def __init__(self):
        self.materialMap = {}
        self.rendererAliases = {
            "Karma": ["Karma", "Mantra"],
            "Mantra": ["Mantra", "Karma"],
            "Redshift": ["Redshift"],
            "Redshift_USD": ["Redshift_USD", "Redshift"],
            "Arnold": ["Arnold"],
            "Renderman": ["Renderman"],
        }
        self.materialAliases = {
            "Karma": ["Karma", "Principled Shader"],
            "Principled Shader": ["Principled Shader", "Karma"],
            "Redshift Material": ["Redshift Material", "Redshift_USD"],
            "Redshift_USD": ["Redshift_USD", "Redshift Material"],
            "Standard Surface": ["Standard Surface"],
            "Pixar Surface": ["Pixar Surface"],
        }
        

    def registerMaterial(self, rendererName, materialType, materialCreator):
        if rendererName not in self.materialMap:
            self.materialMap[rendererName] = {materialType : materialCreator}

        else:
            self.materialMap[rendererName].update({materialType:materialCreator})
        

    def getRegisteredMaterials(self, rendererName):
        return self.materialMap.get(rendererName, {})

    def resolveRenderer(self, rendererName):
        candidates = self.rendererAliases.get(rendererName, [rendererName])
        for candidate in candidates:
            if candidate in self.materialMap:
                return candidate
        return rendererName

    def resolveMaterial(self, rendererName, materialType):
        materials = self.getRegisteredMaterials(rendererName)
        if materialType in materials:
            return materialType

        for alias in self.materialAliases.get(materialType, [materialType]):
            if alias in materials:
                return alias

        if len(materials) == 1:
            return next(iter(materials.keys()))

        return materialType

    def getRegistrationSnapshot(self):
        snapshot = {}
        for renderer_name, materials in self.materialMap.items():
            snapshot[renderer_name] = sorted(materials.keys())
        return snapshot

    def createMaterial(self, rendererName, materialType, assetData, importParams, importOptions):
        resolvedRenderer = self.resolveRenderer(rendererName)
        materials = self.getRegisteredMaterials(resolvedRenderer)
        resolvedMaterial = self.resolveMaterial(resolvedRenderer, materialType)

        if resolvedMaterial not in materials:
            available = ", ".join(sorted(materials.keys())) if materials else "none"
            raise RuntimeError(
                "No material creator registered for renderer '{0}' material '{1}'. Available: {2}".format(
                    resolvedRenderer, resolvedMaterial, available
                )
            )

        return materials[resolvedMaterial](assetData,importParams, importOptions)


# Metaclass implementation that ensures implementation of a creator function
class MaterialsBase:
    def __init__(self):
        pass




