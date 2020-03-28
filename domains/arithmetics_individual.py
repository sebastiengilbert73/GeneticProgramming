import genetic_programming
import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

class ArithmeticsInterpreter(genetic_programming.Interpreter):
    def __init__(self, domainFunctionsTree: ET.ElementTree):
        super().__init__(domainFunctionsTree)

    def Evaluate(self, individual: genetic_programming.Individual, variableToValueDict: Dict[str, str]) -> Any:
        return -1.0

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)-15s %(levelname)s %(message)s')

    logging.info("arithmetics_individual.py __main__")

    functions_tree: ET.ElementTree = ET.parse('./arithmetics.xml')
    interpreter: ArithmeticsInterpreter = ArithmeticsInterpreter(functions_tree)
