import logging
import abc
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Set, Optional, Union
import ast

class Individual(abc.ABC):
    """
    Abstract class an individual class must inherit
    """

    def __init__(self, tree: ET.ElementTree):
        super().__init__()
        self._tree = tree

    """@abc.abstractmethod
    def Cost(self, inputData: Any, targetOutputData: Any) -> float:
        pass
    """


class FunctionSignature():
    def __init__(self, parameterTypesList: List[str], returnType: str) -> None:
        self._parameterTypesList = parameterTypesList
        self._returnType = returnType





class Interpreter(abc.ABC):
    def __init__(self, domainFunctionsTree: ET.ElementTree) -> None:
        super().__init__()
        _domainFunctionsTree = domainFunctionsTree

        # Create dictionaries from function name to parameters
        self._functionNameToSignatureDict: Dict[str, FunctionSignature] = {}

        # Check that each function name is unique
        root: ET.Element = _domainFunctionsTree.getroot()
        functionNamesSet: Set = set()
        for rootChild in root:
            #print("rootChild = {}".format(rootChild))
            #print ("rootChild.tag = {}".format(rootChild.tag))
            if rootChild.tag == 'function':
                functionNameElm: Optional[ET.Element] = rootChild.find('name')
                if functionNameElm is None:
                    raise ValueError("genetic_programming.py Interpreter.__init__(): A function doesn't have a <name> element")
                functionName: Optional[str] = functionNameElm.text
                if functionName is None:
                    raise ValueError(
                        "genetic_programming.py Interpreter.__init__(): A function have an empty <name> element")
                if functionName in functionNamesSet:
                    raise ValueError("genetic_programming.py Interpreter.__init__(): The function name '{}' is encountered more than once in the domain functions tree".format(functionName))
                functionNamesSet.add(functionName)

                parameterTypesElm: Optional[ET.Element] = rootChild.find('parameter_types')
                if parameterTypesElm is None:
                    raise ValueError(
                        "genetic_programming.py Interpreter.__init__(): The function {} doesn't have a <parameter_types> element".format(functionName))
                parameterTypesListStr: Optional[str] = parameterTypesElm.text
                if parameterTypesListStr is None:
                    raise ValueError("genetic_programming.py Interpreter.__init__(): The function {} have an empty <parameter_types> element.".format(
                        functionName))
                parameterTypesListStr = parameterTypesListStr.replace(' ', '')
                parameterTypesListStr = parameterTypesListStr.replace('[', "['")
                parameterTypesListStr = parameterTypesListStr.replace(']', "']")
                parameterTypesListStr = parameterTypesListStr.replace(',', "','")
                #print ("genetic_programming.py Interpreter.__init__(): parameterTypesListStr = {}".format(parameterTypesListStr))
                parameterTypesList = ast.literal_eval(parameterTypesListStr)
                #print ("genetic_programming.py Interpreter.__init__(): parameterTypesList = {}".format(parameterTypesList))

                returnTypeElm: Optional[ET.Element] = rootChild.find('return_type')
                if returnTypeElm is None:
                    raise ValueError(
                        "genetic_programming.py Interpreter.__init__(): The function {} doesn't have a <return_type> element".format(functionName))
                returnType: Optional[str] = returnTypeElm.text
                if returnType is None:
                    raise ValueError(
                        "genetic_programming.py Interpreter.__init__(): The function {} have an empty <return_type> element".format(
                            functionName))

                signature: FunctionSignature = FunctionSignature(parameterTypesList, returnType)
                self._functionNameToSignatureDict[functionName] = signature
            else:
                raise ValueError("genetic_programming.py Interpreter.__init__(): An child of the root element has tag '{}'".format(rootChild.tag))

    def TypeConverter(self, type: str, value: str) -> Any:
        if type == 'float':
            return float(value)
        elif type == 'int':
            return int(value)
        elif type == 'bool':
            if value.lower() in ['true', 'yes']:
                return True
            else:
                return False
        elif type == 'string':
            return value
        else:
            raise NotImplementedError("Interpreter.TypeConverter(): The type {} is not implemented".format(type))

    def Evaluate(self, individual: Individual, variableNameToTypeDict: Dict[str, str], variableNameToValueDict: Dict[str, Any],
                        expectedReturnType: Any) -> Any:
        individualRoot: ET.Element = individual._tree.getroot()
        if len(list(individualRoot)) != 1:
            raise ValueError("Interpreter.Evaluate(): The root has more than one children ({})".format(len(list(individualRoot))))
        headElement = list(individualRoot)[0]
        return self.EvaluateElement(headElement, variableNameToTypeDict, variableNameToValueDict, expectedReturnType)

    def EvaluateElement(self, element: ET.Element, variableNameToTypeDict: Dict[str, str], variableNameToValueDict: Dict[str, Any],
                        expectedReturnType: Any) -> Any:
        childrenList: List[ET.Element] = list(element)
        elementTag = element.tag

        if elementTag == 'constant':
            valueStr: Optional[str] = element.text
            if valueStr is None:
                raise ValueError("Interpreter.EvaluateElement(): A constant has no value")
            return self.TypeConverter(expectedReturnType, valueStr)
        elif elementTag == 'variable':
            variableName: Optional[str] = element.text
            if variableName is None:
                raise ValueError("Interpreter.EvaluateElement(): A variable has no name")
            return variableNameToValueDict[variableName]
        else: # Function
            self.CheckIfSignatureMatches(elementTag, childrenList, variableNameToTypeDict, expectedReturnType)
            childrenEvaluationsList: List[Any] = []
            for childNdx in range(len(childrenList)):
                childExpectedReturnType = self._functionNameToSignatureDict[elementTag]._parameterTypesList[childNdx]
                childEvaluation: Any = self.EvaluateElement(childrenList[childNdx], variableNameToTypeDict, variableNameToValueDict, childExpectedReturnType)
                childrenEvaluationsList.append(childEvaluation)
            return self.FunctionDefinition(elementTag, childrenEvaluationsList)


    @abc.abstractmethod
    def FunctionDefinition(self, functionName: str, argumentsList: List[Any]) -> Any:
        pass

    def CheckIfSignatureMatches(self, functionName: str, argumentsList: List[ET.Element], variableNameToTypeDict: Dict[str, str],
                                expectedReturnType) -> None:
        #print ("CheckIfSignatureMatches(): functionName = {}".format(functionName))
        expectedSignature: FunctionSignature = self._functionNameToSignatureDict[functionName]
        if len(argumentsList) != len(expectedSignature._parameterTypesList):
            raise ValueError("Interpreter.CheckIfSignatureMatches(): len(argumentsList) ({}) != len(expectedSignature._parameterTypesList) ({})".format(
                len(argumentsList), len(expectedSignature._parameterTypesList)
            ))
        for argumentNdx in range(len(argumentsList)):
            argumentTag = argumentsList[argumentNdx].tag
            if argumentTag == 'variable':
                variableName: Optional[str] = argumentsList[argumentNdx].text
                if variableName is None:
                    raise ValueError("Interpreter.CheckIfSignatureMatches(): An variable argument has no name")
                argumentType: Optional[str] = variableNameToTypeDict[variableName]
                if argumentType is None:
                    raise ValueError("Interpreter.CheckIfSignatureMatches(): The variable name {} is not in variableNameToTypeDict".format(variableName))
            elif argumentTag == 'constant':
                argumentType = expectedSignature._parameterTypesList[argumentNdx] # Will be cast at evaluation
            else: # Function
                argumentType = self._functionNameToSignatureDict[argumentTag]._returnType

            if argumentType != expectedSignature._parameterTypesList[argumentNdx]:
                raise ValueError("Interpreter.CheckIfSignatureMatches(): Expected paremter type {}, got argument type {}".format(expectedSignature._parameterTypesList[argumentNdx], argumentType))

        if expectedReturnType != expectedSignature._returnType:
            raise ValueError("Interpreter.CheckIfSignatureMatches(): The expected return type ({}) do not match the function signature return type ({})".format(expectedReturnType, expectedSignature._returnType))




class ArithmeticsInterpreter(Interpreter):

    def FunctionDefinition(self, functionName: str, argumentsList: List[ Union[float, bool] ]) -> Union[float, bool]:
        if functionName == "addition_float":
            floatArg1: float = float(argumentsList[0])
            floatArg2: float = float(argumentsList[1])
            return floatArg1 + floatArg2
        elif functionName == "subtraction_float":
            floatArg1 = float(argumentsList[0])
            floatArg2 = float(argumentsList[1])
            return floatArg1 - floatArg2
        else:
            raise NotImplementedError("ArithmeticsInterpreter.FunctionDefinition(): Not implemented function '{}'".format(functionName))




if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)-15s %(levelname)s %(message)s')

    logging.debug("genetic_programming.py main()")
    domainFunctionsTree: ET.ElementTree = ET.parse('./arithmetics.xml')
    print ("domainFunctionsTree = {}".format(domainFunctionsTree))

    individual: Individual = Individual(ET.parse('./arithmetics_individual_example.xml') )
    interpreter: ArithmeticsInterpreter = ArithmeticsInterpreter(domainFunctionsTree)
    print ("interpreter._functionNameToSignatureDict = {}".format(interpreter._functionNameToSignatureDict))

    variableNameToTypeDict: Dict[str, str] = {'x': 'float', 'y': 'float'}
    variableNameToValueDict: Dict[str, Union[float, bool]] = {'x': 1.0, 'y': 2.0}

    output: float = interpreter.Evaluate(individual, variableNameToTypeDict, variableNameToValueDict, 'float')
    print ("output = {}".format(output))