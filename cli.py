import json
import sys
import copy
import collections

TERMINATORS = [ "jmp", "br", "ret" ]


def form_blocks(func_body):
    blocks = []
    curr_block = []
    
    for instr in func_body["instrs"]:

        if "op" in instr:
            curr_block.append(instr)

            if instr["op"] in TERMINATORS:
                blocks.append(curr_block)
                curr_block = []

        else:
            blocks.append(curr_block)
            curr_block = [instr]

    blocks.append(curr_block)
    return blocks
                

def lvn_block(block):
    table = collections.OrderedDict()
    var2num = dict()

    for instr in block:
        if instr["op"] == "const":
            value = tuple(["const", instr["value"]])
            table[value] = instr["dest"]
            var2num[instr["dest"]] = list(table).index(value)
        if "args" in instr:
            value_list = [instr["op"]]
            value_list += [var2num[arg] for arg in instr["args"]]
            value = tuple(value_list)

            if value in table:
                instr["op"] = "id"
                instr["args"] = [table[value]]
            else:
                if "dest" in instr:
                    table[value] = instr["dest"]
                    if instr["op"] != "const":
                        for i, arg in enumerate(instr["args"]):
                            instr["args"][i] = table[list(table)[var2num[arg]]]

            if "dest" in instr:
                num = list(table).index(value)
                var2num[instr["dest"]] = num
        #print(table)
        #print(var2num)


def lvn(prog):
    for func in prog["functions"]:
        blocks = form_blocks(func)

        for block in blocks:
            lvn_block(block)
    
        func["instrs"] = [instr for instr in block for block in blocks]



def tdce(old_prog):
    last_def = dict()
    prog = copy.deepcopy(old_prog)
    for func in prog["functions"]:
        blocks = form_blocks(func)
        for block in blocks:
            last_def = dict()
            to_delete = set()
            for idx, instr in enumerate(block):
                if "args" in instr:
                    for arg in instr["args"]:
                        if arg in last_def:
                            last_def.pop(arg)

                if "dest" in instr and instr["dest"] in last_def:
                    to_delete.add(idx)

                if "dest" in instr:
                    last_def[instr["dest"]] = instr

            for idx in sorted(to_delete, reverse=True):
                del block[idx]

        func["instrs"] = [instr for instr in block for block in blocks]
    return prog


def dce(old_prog):
    prog = copy.deepcopy(old_prog)
    for func in prog["functions"]:
        used = set()
        to_delete = list()

        for instr in func["instrs"]:
            if "args" in instr:
                used.update(instr["args"])

        for idx, instr in enumerate(func["instrs"]):
            if "dest" in instr and instr["dest"] not in used:
                to_delete.append(idx)

        for idx in sorted(to_delete, reverse=True):
            del func["instrs"][idx]
    return prog


def dce1(prog):
    old_prog = copy.deepcopy(prog)
    while dce(old_prog) != old_prog: old_prog = dce(old_prog)
    return old_prog

def dce2(prog):
    old_prog = copy.deepcopy(prog)
    while dce(old_prog) != old_prog: old_prog = tdce(old_prog)
    return old_prog

if __name__ == "__main__":
    prog = json.loads(sys.stdin.read())
    lvn(prog)
    print(json.dumps(dce2(dce(prog))))