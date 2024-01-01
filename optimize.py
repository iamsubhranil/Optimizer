import sys
contents = None
with open(sys.argv[1], "r") as f:
    contents = "".join(f.readlines())

def lex(contents):
    token_types = {"+": "plus", "-": "minus", "*": "mult", "/": "div",
                   "%": "percen", "=": "equals", ">": "greater",
                   "<": "less", ">=": "greatereq", "<=": "lesseq",
                   "==": "equals_equals", "!=": "not_equals", "||": "or",
                   "&": "and", "(": "open_brace", ")": "close_brace",
                   "{": "open_curl", "}": "close_curl", ";": "semicolon"}

    keywords = ["while", "if", "for", "do", "else"]
    ignore = [' ', '\t', '\n', '\r']
    # token = (type, str)
    size = len(contents)
    i = 0

    tokens = []
    line = 0
    char = 0
    lastlineend = 0
    while i < size:
        if contents[i] in ignore:
            while i < size and contents[i] in ignore:
                if contents[i] == '\n':
                    line += 1
                    lastlineend = i
                    char = 0
                i += 1
        elif contents[i] in token_types.keys():
            t = contents[i]
            char = i - lastlineend
            if i < size and contents[i:i + 2] in token_types.keys():
                t = contents[i:i + 2]
            tokens.append((token_types[t], t, (line, char)))
            i += len(t)
        elif contents[i].isalpha() or contents[i].isnumeric():
            j = i
            char = i - lastlineend
            while j < size and (contents[j].isalpha() or contents[j].isnumeric()):
                j += 1
            part = contents[i:j]
            if part in keywords:
                tokens.append((part, part, (line, char)))
            else:
                tokens.append(("number" if part.isnumeric() else "identifier", part, (line, char)))
            i = j
        else:
            raise RuntimeError("Invalid character", contents[i])
    return tokens

def print_token(token):
    print(token[1], "(" + token[0] + ")", end = ' ')

def print_tokens(tokens):
    curline = 0
    for token in tokens:
        if token[2][0] != curline:
            print()
            curline = token[2][0]
        print_token(token)

# statements = [stmt]
# stmt = assign | while
# while = while (expr) { statements }
# assign = identifier "=" expr
# expr = equality
# equality = greater "==" greater | greater "!=" greater
# greater = lesser ">" lesser | lesser ">=" lesser
# lesser = add "<" add | add "<=" add
# add = mult + add | mult - add
# mult = unit * mult | unit / mult
# unit = identifier | number | "(" expr ")"

def show_err(text, token):
    print(text)
    info = token[2]
    line = info[0]
    start = info[1]
    length = len(token[1])

    linestr = contents.split("\n")[line]
    print(str(line) + ":", linestr)
    print(str(line) + ":", (" " * (start - 1)) + ("^" * length))

    raise RuntimeError("Error in parsing")

def parse_unit(tokens):
    unit = tokens.pop(0)
    if unit[0] == "identifier" or unit[0] == "number":
        return ("unit", unit)
    if unit[0] == "open_brace":
        expr = parse_expr(tokens)
        close = tokens.pop(0)
        if close[0] != "close_brace":
            show_err("Unclosed brace at", close)
        return ("unit_expr", expr)
    show_err("Unexpected unit at", unit)

def parse_binary(tokens, syms, name, next_level, assoc = False):
    left = next_level(tokens)
    if len(tokens) > 0 and tokens[0][1] in syms:
        if assoc:
            return (name, left, tokens.pop(0), parse_binary(tokens, syms, name, next_level, assoc))
        return (name, left, tokens.pop(0), next_level(tokens))
    return left

def parse_mult(tokens):
    return parse_binary(tokens, ("*", "/"), "mult", parse_unit, True)

def parse_add(tokens):
    return parse_binary(tokens, ("+", "-"), "add", parse_mult, True)

def parse_percen(tokens):
    return parse_binary(tokens, ("%"), "percen", parse_add)

def parse_lesser(tokens):
    return parse_binary(tokens, ("<", "<="), "lesser", parse_percen)

def parse_greater(tokens):
    return parse_binary(tokens, (">", ">="), "greater", parse_lesser)

def parse_equality(tokens):
    return parse_binary(tokens, ("==", "!="), "equality", parse_greater)

def parse_conditional(tokens):
    return parse_binary(tokens, ("||", "&"), "conditional", parse_equality)

def parse_assign(tokens):
    return parse_binary(tokens, ("="), "assign", parse_conditional)

def parse_expr(tokens):
    return parse_assign(tokens)

# def parse_assign(tokens):
#    iden = tokens.pop(0)
#    if iden[0] != "identifier":
#        show_err("Invalid assign statement at", iden)
#    if tokens.pop(0)[0] != "equals":
#        show_err("Expected = after identifier at", iden)
#    return ("assign", iden, parse_expr(tokens))

def parse_block(tokens, keyword, name):
    if tokens.pop(0)[0] != "open_curl":
        show_err("Expected '{' after", name, "at", keyword)
    stmts = []
    while tokens[0][0] != "close_curl":
        stmts.append(parse_stmt(tokens))
    tokens.pop(0)
    return stmts

def parse_while(tokens):
    wh = tokens.pop(0)
    cond = parse_expr(tokens)
    stmts = parse_block(tokens, wh, "while")
    return ("while", cond, stmts)

def parse_if(tokens):
    if_ = tokens.pop(0)
    cond = parse_expr(tokens)
    stmts = parse_block(tokens, if_, "if")
    rest = None
    if tokens[0][0] == "else":
        else_ = tokens.pop(0)
        if tokens[0][0] == "if":
            rest = ("elseif", parse_if(tokens))
        else:
            else_stmts = parse_block(tokens, else_, "else")
            rest = ("else", else_stmts)
    return ("if", cond, stmts, rest)

def expect(tokens, what, after, keyword):
    # print(tokens[0][1])
    if tokens[0][1] != what:
        show_err("Expected '" + what + "' after " + after, keyword)
    return tokens.pop(0)

def parse_do(tokens):
    do = tokens.pop(0)
    stmts = parse_block(tokens, do, "do")
    expect(tokens, "while", "do", do)
    cond = parse_expr(tokens)
    return ("do", cond, stmts)

def parse_for(tokens):
    for_ = tokens.pop(0)
    expect(tokens, "(", "for", for_)
    init = parse_assign(tokens)
    expect(tokens, ";", "initialization", for_)
    cond = parse_expr(tokens)
    expect(tokens, ";", "condition", for_)
    incr = parse_assign(tokens)
    expect(tokens, ")", "increment/decrement", for_)
    stmts = parse_block(tokens, for_, "for")
    return ("for", init, cond, incr, stmts)

def parse_stmt(tokens):
    if tokens[0][0] == "while":
        return parse_while(tokens)
    elif tokens[0][0] == "if":
        return parse_if(tokens)
    elif tokens[0][0] == "for":
        return parse_for(tokens)
    elif tokens[0][0] == "do":
        return parse_do(tokens)
    return ("expr", parse_expr(tokens))

def parse_statements(tokens):
    statements = []
    while len(tokens) > 0:
        statements.append(parse_stmt(tokens))
    return statements

def parse(tokens):
    return parse_statements(tokens)

def print_expr(expr, tab=''):
    print("\n" + tab + "|- ", end='')
    if expr[0] == 'unit':
        print(expr[1][1], end='')
    elif expr[0] == 'unit_expr':
        print("( ", end='')
        print_expr(expr[1], tab + '\t')
        print("\n" + tab + "|-", end=' ')
        print(" )", end='')
    else:
        print_token(expr[2])
        print_expr(expr[1], tab + '\t')
        print_expr(expr[3], tab + '\t')

def print_stmt(stmt, tab=''):
    if stmt[0] == 'expr':
        print_expr(stmt[1], tab)
        return
    print("\n" + tab + "|- ", end='')
    if stmt[0] == 'while':
        print("while", end='')
        print_expr(stmt[1], tab + '\t')
        print("\n" + tab + "|- {")
        print_stmts(stmt[2], tab + '\t')
        print("\n" + tab + "|- }")
    elif stmt[0] == 'if':
        print("if", end='')
        print_expr(stmt[1], tab + '\t')
        print("\n" + tab + "|- {")
        print_stmts(stmt[2], tab + '\t')
        print("\n" + tab + "|- }")
        if stmt[3] != None:
            print("\n" + tab + "|- else")
            print("\n" + tab + "|- {")
            if stmt[3][0] == 'else':
                print_stmts(stmt[3][1], tab + '\t')
            else:
                print_stmt(stmt[3][1], tab + '\t')
            print("\n" + tab + "|- }")
    elif stmt[0] == 'do':
        print("do\n" + tab + "|- {")
        print_stmts(stmt[2], tab + '\t')
        print("\n" + tab + "|- }")
        print(tab + "|- while", end='')
        print_expr(stmt[1], tab + '\t')
        print("\n", end='')
    elif stmt[0] == 'for':
        print("for")
        print_expr(stmt[1], tab + '\t')
        print_expr(stmt[2], tab + '\t')
        print_expr(stmt[3], tab + '\t')
        print_stmts(stmt[4], tab + '\t')
    else:
        raise RuntimeError("Unknown statement " + str(stmt[0]))

def print_stmts(stmts, tab=''):
    for stmt in stmts:
        print_stmt(stmt, tab)
        print()

# convert to TAC
# TAC format
# idx: a = b op c
# OR
# idx: jump_if_true/jump_if_false condition_var target_idx

def convert_expr(expr, tacs, temp_vars):
    if expr[0] == 'unit':
        return expr[1][1]
    elif expr[0] == 'unit_expr':
        return convert_expr(expr[1], tacs, temp_vars)
    else:
        left = convert_expr(expr[1], tacs, temp_vars)
        right = convert_expr(expr[3], tacs, temp_vars)
        tvar = "t" + str(len(temp_vars))
        temp_vars.append(tvar)
        tacs.append((expr[2][1], tvar, left, right))
        return tvar

def convert_stmt(stmt, tacs, temp_vars):
    if stmt[0] == 'expr':
        convert_expr(stmt[1], tacs, temp_vars)
    elif stmt[0] == 'while':
        condition_idx = len(tacs)
        cond = convert_expr(stmt[1], tacs, temp_vars)
        patch_idx = len(tacs)
        tacs.append(('jump_if_false', 0, cond))
        for st in stmt[2]:
            convert_stmt(st, tacs, temp_vars)
        tacs.append(('jump', condition_idx))
        tacs[patch_idx] = ('jump_if_false', len(tacs), cond)
    elif stmt[0] == 'do':
        patch_idx = len(tacs)
        for st in stmt[2]:
            convert_stmt(st, tacs, temp_vars)
        res = convert_expr(stmt[1], tacs, temp_vars)
        tacs.append(('jump_if_true', patch_idx, res))
    elif stmt[0] == 'if':
        res = convert_expr(stmt[1], tacs, temp_vars)
        patch_idx = len(tacs)
        tacs.append(('jump_if_false', res, 0))
        for st in stmt[2]:
            convert_stmt(st, tacs, temp_vars)
        tacs[patch_idx] = ('jump_if_false', len(tacs), res)
        if stmt[3] != None:
            patch_jump = len(tacs)
            tacs.append(('jump', 0))
            tacs[patch_idx] = ('jump_if_false', len(tacs), res)
            if stmt[3][0] == 'else':
                for st in stmt[3][1]:
                    convert_stmt(st, tacs, temp_vars)
            else:
                convert_stmt(stmt[3][1], tacs, temp_vars)
            tacs[patch_jump] = ('jump', len(tacs))
    elif stmt[0] == 'for':
        convert_expr(stmt[1], tacs, temp_vars)
        cond_idx = len(tacs)
        cond_var = convert_expr(stmt[2], tacs, temp_vars)
        patch_idx = len(tacs)
        tacs.append(('jump_if_false', 0, cond_var))
        for st in stmt[4]:
            convert_stmt(st, tacs, temp_vars)
        convert_expr(stmt[3], tacs, temp_vars)
        tacs.append(('jump', cond_idx))
        tacs[patch_idx] = ('jump_if_false', len(tacs), cond_var)
    else:
        raise RuntimeError("Unknown statement " + str(stmt[0]))

def convert_to_tac(stmts):
    tacs = []
    temp_vars = []
    for stmt in stmts:
        convert_stmt(stmt, tacs, temp_vars)
    tacs.append(('end',))
    return tacs

def print_tacs(tacs):
    for idx, tac in enumerate(tacs):
        print(str(idx) + ": ", end='')
        if tac[0] == '=':
            print(tac[1], '=', tac[2])
        elif tac[0] == 'end':
            print(tac[0])
        elif tac[0] == 'jump':
            print('jump', tac[1])
        elif tac[0] == 'jump_if_false' or tac[0] == 'jump_if_true':
            print(tac[0], tac[1], tac[2])
        else:
            print(tac[1], '=', tac[2], tac[0], tac[3])

# Basic blocks
# format:
# array of tuples [(instructions, pred, succ) ...]
# each tuple containing three members:
#   instructions: array of instructions in the basic block
#   pred: array of indices of predecessors of the basic block
#   succ: array of indices of successors to the basic block

def convert_to_bb(tacs):
    basic_blocks = []
    leaders = [0]
    for idx, t in enumerate(tacs):
        if t[0] == 'jump' or t[0] == 'jump_if_false' or t[0] == 'jump_if_true':
            if t[1] not in leaders:
                leaders.append(t[1])
            if idx + 1 not in leaders:
                leaders.append(idx + 1)
    leaders.sort()

    for _ in leaders:
        basic_blocks.append([[], [], []])

    for idx, l in enumerate(leaders):
        start = l
        end = len(tacs)
        if idx != len(leaders) - 1:
            end = leaders[idx + 1]
        instructions = tacs[start:end]
        succ = basic_blocks[idx][2]
        if instructions[-1][0] == 'jump' or instructions[-1][0] == 'jump_if_false' or instructions[-1][0] == 'jump_if_true':
            dest_block = leaders.index(instructions[-1][1])
            succ.append(dest_block)
            basic_blocks[dest_block][1].append(idx)
            if instructions[-1][0] == 'jump':
                instructions[-1] = (instructions[-1][0], dest_block)
            else:
                instructions[-1] = (instructions[-1][0], dest_block, instructions[-1][2])
        if instructions[-1][0] != 'jump':
            if idx != len(leaders) - 1:
                succ.append(idx + 1)
                basic_blocks[idx + 1][1].append(idx)

        basic_blocks[idx][0] = instructions

    return basic_blocks

def print_bb(basic_blocks):
    print()
    print()
    for idx, block in enumerate(basic_blocks):
        print("// block #" + str(idx), ", preds:", block[1], " succs:", block[2])
        print_tacs(block[0])
        print()
        print()

if __name__ == "__main__":
    tokens = lex(contents)
    # print_tokens(tokens)
    tree = parse(tokens)
    print_stmts(tree)
    tacs = convert_to_tac(tree)
    print_tacs(tacs)
    bb = convert_to_bb(tacs)
    print_bb(bb)
