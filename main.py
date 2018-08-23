import karelia
import random
import sys
import time
import json

def get_saved_rolls():
    with open('saved_rolls.json') as f:
        saved_rolls = json.loads(f.read())
    return saved_rolls

def write_saved_rolls(saved_rolls):
    with open('saved_rolls.json', 'w') as f:
        f.write(json.dumps(saved_rolls))

def parse(roll_text):
    """
    >>> result = parse(2d8+10)
    >>> 11 < result < 27
    True

    """

    # Disadvantage rolls
    if "dd" in roll_text or roll_text == "disadv":
        # Simple 2d20 disadvantage
        if roll_text == "disadv":
            rolls = 2
            dice = 20
            mod = 0

        # Complex disadvantage
        else:
            # Check to see if a modifier is included
            try:
                roll, mod = roll_text.split('+')
                mod = int(mod)
            except ValueError:
                roll = roll_text
                mod = 0

            # Split into dice type and number of rolls
            try:
                rolls, dice = roll.split('dd')
            except:
                return "Unparsable command {roll_text}."
            
        roll_output = sorted([random.randint(1, int(dice)) for _ in range(int(rolls))])

        if mod > 0:
            mod_text = f" + mod{mod}"
        else:
            mod_text = ''
            
        output = f"Result {roll_output[0]+mod}: {', '.join([str(res) for res in roll_output])}{mod_text}"
        return output

    # Advantages
    elif "ad" in roll_text or roll_text == "adv":
        if roll_text == "adv":
            rolls = 2
            dice = 20
            mod = 0
            
        else:
            # Check to see if a modifier is included
            try:
                roll, mod = roll_text.split('+')
                mod = int(mod)
            except ValueError:
                roll = roll_text
                mod = 0

            # Split into dice type and number of rolls
            try:
                rolls, dice = roll.split('ad')
            except:
                return "Unparsable command {roll_text}."
            
        roll_output = sorted([random.randint(1, int(dice)) for _ in range(int(rolls))], reverse=True)

        if isinstance(mod, int):
            mod_text = f" + mod{mod}"
        else:
            mod_text = ''
        output = f"Result {roll_output[0]+mod}: {', '.join([str(res) for res in roll_output])}{mod_text}"
        return output
    
    try:
        roll, mod = roll_text.split('+')
        mod = int(mod)
    except ValueError:
        roll = roll_text
        mod = 0

    try:
        rolls, dice = roll.split('d')
    except ValueError:
        rolls = 1
        dice = roll
        
    if rolls == '': rolls = 1
    if dice == '': dice = 20

    rolls = int(rolls)
    dice = int(dice)

    if not 0 < rolls <= 20:
        return "You can have 1-20 rolls inclusive."
    if not 0 < dice <= 20:
        return "You can roll die of 1-20 sides inclusive."
    
    try:
        roll_output = [random.randint(1, int(dice)) for _ in range(int(rolls))]
    except ValueError:
        return("That made *no* sense...")
        
    if isinstance(mod, int):
        mod_text = f" + mod{mod}"
    else:
        mod_text = ''
    output = f"Total {sum(roll_output)+mod}: {', '.join([str(res) for res in roll_output])}{mod_text}"

    return output


roller = karelia.bot('Roller', 'test')
roller.stock_responses['long_help'] = """I roll dice.
You can invoke a roll with !roll, !r, /roll and /r.
The following syntax simply rolls 1 D20: !r 1d20
The number of rolls defaults to 1, and the dice type to D20.

A modifier can be added with !r 1d20+2. (Please note, in the case of a negative modifier, it should be expressed as !1d20+-2.)

For a 2d20 advantage roll, !r adv.
For a 2d20 disadvantage roll, !r disadv.

For an complex advantage roll, !r 2ad20(+10).
For a complex disadvantage roll, !r 2dd20(+10).

Save a formula: !save staff = 2d20+5
Run a formula: !roll staff
See a list of saved formulae: !list saved
Delete a formula: !rm staff

Pouncy referenced this webpage while creating this bot: http://dnd.wizards.com/products/tabletop/players-basic-rules"""

while True:
    try:
        roller.connect()
        while True:
            msg = roller.parse()
            if msg.type == "send-event":
                if msg.data.content.split()[0] in ['!roll', '!r', '/roll', '/r']:

                    # Load up and check command against saved rolls
                    saved_rolls = get_saved_rolls()
                    if msg.data.content.split()[1] in saved_rolls.keys():
                        try:
                            roller.reply(parse(saved_rolls[msg.data.content.split()[1]]))
                        except:
                            roller.reply(f"Sorry, couldn't parse roll {msg.data.content.split()[1]}.")
                    else:
                        try:
                            roller.reply(parse(msg.data.content.split()[1]))
                        except:
                            roller.reply(f"Sorry, couldn't parse roll {msg.data.content.split()[1]}.")

                # Allows rolls to be named and saved
                elif msg.data.content.split()[0] == '!save':
                    roll_name = msg.data.content.split()[1]
                    roll_formula = msg.data.content.split()[3]
                    
                    saved_rolls = get_saved_rolls()
                    saved_rolls[roll_name] = roll_formula
                    write_saved_rolls(saved_rolls)
                    
                    roller.reply(f"Saved roll {roll_name}, corresponding to {roll_formula}.")

                # List saved rolls
                elif msg.data.content == "!list saved":
                    saved_rolls = get_saved_rolls()
                    roller.reply("\n".join([f"{key}: {value}" for key, value in saved_rolls.items()]))

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
    
            
