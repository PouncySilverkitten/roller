import doctest
import json
import random
import re
import sys
import time
from itertools import filterfalse

import karelia


class RollsTooHigh(Exception): pass
class RollsTooLow(Exception): pass

class SidesTooHigh(Exception): pass
class SidesTooLow(Exception): pass

class BadRollSyntax(Exception): pass

def get_saved_rolls():
    with open('saved_rolls.json') as f:
        saved_rolls = json.loads(f.read())
    return saved_rolls


def write_saved_rolls(saved_rolls):
    with open('saved_rolls.json', 'w') as f:
        f.write(json.dumps(saved_rolls))


def sep(rolls):
    """
    >>> sep('2d20')
    ['2d20']
    >>> sep('2d20+2')
    ['2d20', '+', '2']
    >>> sep('2d20-3')
    ['2d20', '-', '3']
    >>> sep('2d20+6d4')
    ['2d20', '+', '6d4']
    >>> sep('2d20-2+2d6-3')
    ['2d20', '-', '2', '+', '2d6', '-', '3']
    >>> sep('2d20-2d6-2-4')
    ['2d20', '-', '2d6', '-', '2', '-', '4']
    """


    all_bits = []

    pos_bits = flatten([['+', roll] for roll in rolls.split('+')])[1:] 
    for bit in pos_bits:
        if '-' not in bit:
            all_bits.append(bit)
            continue
        spl = bit.split('-')
        all_bits.append(spl[0])
        for i in range(1, len(spl)):
            all_bits.append('-')
            all_bits.append(spl[i])

    return all_bits

flatten = lambda l: [item for sublist in l for item in sublist]


def lookup(saved_rolls, roll, sender):
    """
    >>> saved = {'Irinora': {'staff': '2d20+2', 'amulet': '2d10-1'}, 'Verasar Alamelis': {'staff': '4d8+3', 'amulet': '3d6+4'}}
    >>> lookup(saved, 'staff', 'Akunusella')
    'staff'
    >>> lookup(saved, 'trinket', 'Vexildah')
    'trinket'
    >>> lookup(saved, 'amulet', 'Verasar Alamelis')
    '3d6+4'
    >>> lookup(saved, 'adv', '')
    '2ad20'
    >>> lookup(saved, 'disadv', '')
    '2dd20'
    """

    if roll == 'adv':
        return '2ad20'
    elif roll == 'disadv':
        return '2dd20'

    try:
        return saved_rolls[sender][roll]
    except KeyError:
        return roll


def parse(part):
    p = list(filter(None, re.split("a|d", part)))
    # If int
    try:
        if 'd' not in part and len(p) == 1: return (int(p[0]), p[0])

        # If no number of rolls specified
        if len(p) == 1: p = [1, p[0]]
        p = list(map(int, p))
    except ValueError:
        raise BadRollSyntax

    # Sanity check
    if p == [] or int(p[0]) < 1:
        raise RollsTooLow
    elif int(p[1]) < 4:
        raise SidesTooLow
    elif int(p[0]) > 20:
        raise RollsTooHigh
    elif int(p[1]) > 100:
        raise SidesTooHigh
    rolls = sorted([random.randint(1, p[1]) for _ in range(p[0])])
    if 'dd' in part:
        total = rolls[0]
    elif "ad" in part:
        total = rolls[-1]
    else:
        total = sum(rolls)

    return (total, ', '.join([str(r) for r in rolls]),)

def assembler(roll_parts):
    output = "{}: "
    parsed = parse(roll_parts[0])
    total = parsed[0]
    output += "({})".format(str(parsed[1]))
    i = 1
    while i < len(roll_parts):
        # Possibilities are roll, +, -, int
        parsed = parse(roll_parts[i+1])
        if roll_parts[i] == '-':
            total -= parsed[0]
            output += " - ({})".format(parsed[1])
        else:
            total += parsed[0]
            output += " + ({})".format(parsed[1])

        i += 2

    return output.format(total)


roller = karelia.bot('Roller', 'test')
roller.stock_responses['long_help'] = """I roll dice.
You can invoke a roll with !roll, !r, /roll and /r.
The following syntax simply rolls 1 D20: !r 1d20
The number of rolls defaults to 1, and the dice type to D20.

A modifier can be added with !r 1d20+2.

For a 2d20 advantage roll, !r adv.
For a 2d20 disadvantage roll, !r disadv.

For an complex advantage roll, !r 2ad20(+10).
For a complex disadvantage roll, !r 2dd20(+10).

Save a formula: !save 2d20+5 staff
Run a formula: !roll staff
See a list of saved formulae: !list saved
Delete a formula: !rm staff

Pouncy referenced this webpage while creating this bot: http://dnd.wizards.com/products/tabletop/players-basic-rules"""

def main():
    while True:
        try:
            roller.connect()
            while True:
                msg = roller.parse()
                if msg.type == "send-event":

                    if msg.data.content.split()[0] in ['!roll', '!r', '/roll', '/r']:
                        reply = ""
                        try:
                            frags = sep(msg.data.content.split()[1])
                            saved = get_saved_rolls()
                            sender = msg.data.sender.name
                            looked_up = flatten([sep(lookup(saved, frag, sender)) for frag in frags])
                            reply = assembler(looked_up)

                        except SidesTooHigh:
                            reply = "Sorry, the max number of sides is 100."
                        except SidesTooLow:
                            reply = "Sorry, your dice must have at least 4 sides."

                        except RollsTooHigh:
                            reply = "Sorry, the max number of rolls is 20."
                        except RollsTooLow:
                            reply = "Sorry, you need to roll at least one die."

                        except BadRollSyntax:
                            reply = "Sorry, couldn't interpret that roll."

                        finally:
                            roller.reply(reply)

                    # Allows rolls to be named and saved
                    elif msg.data.content.split()[0] == '!save':
                        if len(msg.data.content.split()) == 3:
                            roll_name = msg.data.content.split()[2]
                            roll_formula = msg.data.content.split()[1]

                            try:
                                frags = sep(roll_formula)
                                saved = get_saved_rolls()
                                sender = msg.data.sender.name
                                looked_up = [lookup(saved, frag, sender) for frag in frags]
                                assembler(looked_up)

                                saved_rolls = get_saved_rolls()
                                roll_cat = msg.data.sender.name
                                if roll_cat not in saved_rolls:
                                    saved_rolls[roll_cat] = {}
                                saved_rolls[roll_cat][roll_name] = roll_formula
                                write_saved_rolls(saved_rolls)
                                reply = "Saved roll {}, corresponding to {}.".format(roll_name, roll_formula)

                            except SidesTooHigh:
                                reply = "Sorry, the max number of sides is 100."
                            except SidesTooLow:
                                reply = "Sorry, your dice must have at least 4 sides."

                            except RollsTooHigh:
                                reply = "Sorry, the max number of rolls is 20."
                            except RollsTooLow:
                                reply = "Sorry, you need to roll at least one die."

                            except BadRollSyntax:
                                reply = "Sorry, couldn't interpret that roll."

                            finally:
                                roller.reply(reply)

                        else:
                            roller.reply("Syntax is !save 2d20+2 name")
                            continue

                    # List saved rolls
                    elif msg.data.content == "!list saved":
                        saved_rolls = get_saved_rolls()
                        reply = ""
                        for key in saved_rolls:
                            reply += "{}:\n".format(key)
                            for _key, value in saved_rolls[key].items():
                                reply += "    {}: {}\n".format(_key, value)
                            reply += "\n"
                        roller.reply(reply)

                    # Delete saved rolls
                    elif msg.data.content.startswith('!rm '):
                        saved_rolls = get_saved_rolls()
                        try:
                            del saved_rolls[msg.data.content.split()[1]]
                            write_saved_rolls(saved_rolls)
                            roller.reply("Deleted.")
                        except:
                            roller.reply("Sorry, couldn't delete it.")

        except KeyboardInterrupt:
            sys.exit(0)
        except:
            roller.log()
            roller.disconnect()
        finally:
            time.sleep(1)

if __name__ == "__main__":
    #doctest.testmod()
    main()
