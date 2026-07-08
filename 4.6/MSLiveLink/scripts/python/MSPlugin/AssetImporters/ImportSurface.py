from ..Utilities.SingletonBase import Singleton
from ..MaterialsSetup.MaterialsCreator import MaterialsCreator
from ..MaterialsSetup import *
from ..Utilities.Compatibility import set_first_available_parm
import hou
import os

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
        return node.parmTuple(parmname) is not None

    def importAsset(self, assetData, importOptions, importParams):
        materialsCreator = MaterialsCreator()

        ui_opts = importOptions.get("UI", {})
        import_opts = ui_opts.get("ImportOptions", {})
        usd_opts = ui_opts.get("USDOptions", {})

        enable_usd = import_opts.get("EnableUSD", False)
        renderer = import_opts.get("Renderer", "")
        material_choice = import_opts.get("Material", "")

        if not enable_usd or importParams.get("importType", "") == "Normal":
            return self._import_classic_surface(
                assetData,
                importOptions,
                importParams,
                materialsCreator,
                renderer,
                material_choice,
            )

        return self._import_usd_surface(
            assetData,
            importOptions,
            importParams,
            materialsCreator,
            usd_opts,
            import_opts,
        )

    def _post_import_cleanup(self, importParams, importedSurface):
        material_node = hou.node(importParams["materialPath"])
        if material_node is not None:
            material_node.moveToGoodPosition()
            try:
                material_node.layoutChildren()
            except Exception:
                pass

        mat_network = hou.node("/mat")
        if mat_network is not None:
            mat_network.moveToGoodPosition()

        try:
            importedSurface.setSelected(True)
        except Exception:
            pass

        return importedSurface

    def _create_renderer_container(self, renderer, importParams):
        material_root = hou.node(importParams["materialPath"])
        if material_root is None:
            raise RuntimeError("Material path does not exist: {0}".format(importParams["materialPath"]))

        if renderer == "Redshift":
            container = material_root.createNode("redshift_vopnet", importParams["assetName"], run_init_scripts=False)
            importParams["materialPath"] = container.path()
            self._add_redshift_viewport_parms(container)
            return container

        if renderer == "Arnold":
            container = material_root.createNode("arnold_materialbuilder", importParams["assetName"], run_init_scripts=False)
            importParams["materialPath"] = container.path()
            return container

        if renderer == "Octane":
            container = material_root.createNode("octane_vopnet", importParams["assetName"], run_init_scripts=False)
            importParams["materialPath"] = container.path()
            return container

        if renderer == "Renderman":
            container = material_root.createNode("pxrmaterialbuilder", importParams["assetName"], run_init_scripts=False)
            importParams["materialPath"] = container.path()
            return container

        return None

    def _add_redshift_viewport_parms(self, redshiftContainer):
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
                hou.ToggleParmTemplate("ogl_use_tex1", "Display Texture", default_value=True),
            ],
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
                hou.FloatParmTemplate("ogl_tex_uvrotate1", "Rotate", 1, default_expression=[("ch(\"albedo/rotate\")")], default_expression_language=(hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript)),
            ],
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
                hou.FloatParmTemplate("ogl_displace_uvrotate", "UV Rotate", 1, default_expression=[("ch(\"displacement/rotate\")")], default_expression_language=(hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript, hou.scriptLanguage.Hscript)),
            ],
        )

        nodeParamsGroups.append(nodeTexParam)
        nodeParamsGroups.append(nodeAddDispParam)
        nodeParamsGroups.append(nodeAddParam)
        redshiftContainer.setParmTemplateGroup(nodeParamsGroups)

    def _import_classic_surface(self, assetData, importOptions, importParams, materialsCreator, renderer, material_choice):
        container = self._create_renderer_container(renderer, importParams)
        importedSurface = materialsCreator.createMaterial(renderer, material_choice, assetData, importParams, importOptions)
        if container is not None:
            return self._post_import_cleanup(importParams, container)
        return self._post_import_cleanup(importParams, importedSurface)

    def _import_usd_surface(self, assetData, importOptions, importParams, materialsCreator, usd_opts, import_opts):
        usdMaterials = {
            "Karma": "Karma",
            "Renderman": "Pixar Surface",
            "Arnold": "Standard Surface",
            "Redshift_USD": "Redshift_USD",
        }
        usdRendererType = usd_opts.get("USDMaterial", "Karma")
        importedSurface = None
        usdMaterialContainer = None

        if (assetData.get("type") == "surface") or (assetData.get("type") == "atlas" and not import_opts.get("UseAtlasSplitter", False)) or (assetData.get("type") == "brush"):
            usdMaterialContainer = hou.node(importParams["materialPath"]).createNode("materiallibrary", importParams["assetName"])
            importParams["materialPath"] = usdMaterialContainer.path()

        if usdRendererType == "Karma":
            karmaContainer = hou.node(importParams["materialPath"]).createNode("subnet", importParams["assetName"])
            importParams["materialPath"] = karmaContainer.path()
            importedSurface = materialsCreator.createMaterial("Karma", usdMaterials["Karma"], assetData, importParams, importOptions)

        elif usdRendererType == "Redshift_USD":
            importOptions.setdefault("UI", {}).setdefault("USDOptions", {})["Material"] = "Redshift Material"
            importOptions["UI"]["USDOptions"]["Renderer"] = "Redshift"
            redshiftContainer = hou.node(importParams["materialPath"]).createNode("rs_usd_material_builder", importParams["assetName"])
            importParams["materialPath"] = redshiftContainer.path()
            importedSurface = materialsCreator.createMaterial("Redshift_USD", usdMaterials["Redshift_USD"], assetData, importParams, importOptions)

        elif usdRendererType == "Arnold":
            arnoldContainer = hou.node(importParams["materialPath"]).createNode("arnold_materialbuilder", importParams["assetName"], run_init_scripts=False)
            importParams["materialPath"] = arnoldContainer.path()
            importedSurface = materialsCreator.createMaterial("Arnold", usdMaterials["Arnold"], assetData, importParams, importOptions)

            if usdMaterialContainer is not None and assetData.get("type") in ("surface", "atlas"):
                dispValue = "0.008"
                for assetMeta in assetData.get("meta", []):
                    if assetMeta.get("key") == "height":
                        dispValue = str(assetMeta.get("value", "")).split(" ")[0]

                renderSettings = usdMaterialContainer.createOutputNode("rendergeometrysettings")
                set_first_available_parm(
                    renderSettings,
                    ["xn__primvarsarnolddisp_height_uhbg", "primvarsarnolddisp_height", "arnolddisp_height"],
                    dispValue,
                )

            importedSurface = arnoldContainer

        else:
            importedSurface = materialsCreator.createMaterial(usdRendererType, usdMaterials.get(usdRendererType, usdMaterials["Karma"]), assetData, importParams, importOptions)

        if usdMaterialContainer is not None:
            if usdMaterialContainer.parm("matnode1") is not None:
                usdMaterialContainer.parm("matnode1").set(importParams["assetName"])
            if usdMaterialContainer.parm("matpath1") is not None:
                usdMaterialContainer.parm("matpath1").set(importParams["assetName"])

        return self._post_import_cleanup(importParams, importedSurface)
