"""
Конвертує граф у дані для віртуального туру A-Frame
"""
import json

def graph2aframe(input, output):
    with open(input, "r", encoding="utf-8") as file:
        data = json.load(file)

    nodes=data["nodes"]
    edges=data["edges"]

    data2={}
    for nid, nd in nodes.items():
        if nd['description']=='': continue
        data2[nd['label']]=eval(nd['description'])

    with open(output, "w", encoding="utf-8") as file:
        json.dump(data2, file, indent=2)

if __name__=="__main__":
    graph2aframe(input="museum.json", output="data.json")