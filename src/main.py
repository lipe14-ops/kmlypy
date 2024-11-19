from __future__ import annotations
from abc import ABC
import xml.etree.ElementTree as ET
from pathlib import Path

class KMLTag(ABC):
    def __init__(self, namespace: str | None = '', **kwargs):
        self.namespace = namespace
        self.__attributes = kwargs
        self.children: list[KMLTag] = []

    def __repr__(self) -> str:
        return type(self).__name__.replace("KML", '')

    def __str__(self) -> str:
        tag_name = self.__repr__()
        tag_body = '\n'

        for att_name, att_body in self.__attributes.items():
            if att_name and att_body:
                tag_body += f'<{att_name}>{att_body}</{att_name}>\n'

        for child in self.children:
            tag_body += child.__str__() + '\n'

        return f"<{tag_name}>{tag_body}</{tag_name}>"

    def _add_tag(self, tag: KMLTag) -> None:
        self.children.append(tag)


class KMLFolder(KMLTag):
    def __init__(self, namespace: str | None = '', name: str | None = None, description: str | None = None):
        super().__init__(namespace, name=name, description=description)
        self.name = name
        self.description = description
        self.children: list[KMLTag] = []

class KMLDocument(KMLTag):
    def __init__(self, namespace: str | None = '', name: str | None = None, description: str | None = None):
        super().__init__(namespace, name=name, description=description)
        self.name = name
        self.description = description
        self.children: list[KMLTag] = []


def kml_file_explore(tree_root, tag: KMLTag) -> KMLTag:

    for child in tree_root:

        element: KMLTag | None = None

        match child.tag:
            case x if x.endswith('Folder') or x.endswith('Document'):

                container_name = child.find(f'{tag.namespace}name')
                container_description = child.find(f'{tag.namespace}description')

                kml_container_type = KMLFolder if x.endswith('Folder') else KMLDocument
                    
                element = kml_container_type(
                    namespace   = tag.namespace,
                    name        = container_name.text if container_name is not None else None,
                    description = container_description.text if container_description is not None else None
                )

            case _:
                kml_file_explore(child, tag)

        if not element:
            continue

        tag._add_tag(element)
        kml_file_explore(child, element)

    return tag


class KMLFile(object):
    def __init__(self, filepath: Path | str) -> None:
        self.filepath = filepath

    def __enter__(self):
        kml_tree = ET.parse(self.filepath)
        kml_root = kml_tree.getroot()

        namespace = kml_root.tag[: kml_root.tag.index('}') + 1]

        document = KMLDocument(namespace=namespace)
        return kml_file_explore(kml_root, document).children.pop()

    def __exit__(self, exec_type, exec_val, exec_tb) -> None:
        return 
        
def main():

    with KMLFile('./res/file-3.kml') as kml_file:
        print(kml_file)

    return

if __name__ == "__main__":
    main()
