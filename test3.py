from pydantic import BaseModel

glob = []


class Hui(BaseModel):
    name: str


def load_data():
    glob.append(Hui(name="hui 1"))
