from __future__ import annotations
from abc import ABC
import xml.etree.ElementTree as ET
from pathlib import Path

class KMLTag(ABC):
    def __init__(self, **kwargs):
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
    def __init__(self, name: str | None = None, description: str | None = None):
        super().__init__(name=name, description=description)
        self.name = name
        self.description = description
        self.children: list[KMLTag] = []

class KMLDocument(KMLTag):
    def __init__(self, name: str | None = None, description: str | None = None):
        super().__init__(name=name, description=description)
        self.name = name
        self.description = description
        self.children: list[KMLTag] = []


class KMLFileTree(object):
    def __init__(self):
        self.children: list[KMLTag] = []


def parse_kml_file(filepath: Path | str) -> KMLFileTree:
    ...

class KMLFile(object):
    def __init__(self, filepath: Path | str) -> None:
        self.filepath = filepath

    def __enter__(self):
        return parse_kml_file(self.filepath)

    def __exit__(self, exec_type, exec_val, exec_tb) -> None:
        return 
        
def main():
    folder1 = KMLFolder(name='FIRST FOLDER')
    folder2 = KMLFolder()

    folder1._add_tag(folder2)
    print(folder1)

    return

if __name__ == "__main__":
    main()
