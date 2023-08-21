
def Red(skk): return("\033[91m{}\033[00m" .format(skk))
def Green(skk): return("\033[92m{}\033[00m" .format(skk))
def Yellow(skk): return("\033[93m{}\033[00m" .format(skk))
def LightPurple(skk): return("\033[94m{}\033[00m" .format(skk))
def Purple(skk): return("\033[95m{}\033[00m" .format(skk))
def Cyan(skk): return("\033[96m{}\033[00m" .format(skk))
def LightGray(skk): return("\033[97m{}\033[00m" .format(skk))
def Black(skk): return("\033[98m{}\033[00m" .format(skk))


def question(q,required=True):
    while True:
        answer = input(Cyan(q+"\n"))
        if answer == "" and required:
            print(Red("This field is required"))
        else:
            break
    return answer 

def multiple_choice(q,values):
    while True:
        question = q + "\n" + "\n".join([f"{i+1}) {x}" for i,x in enumerate(values)]) + "\n"
        answer = input(Cyan(question))
        try:
            answer = int(answer)
            if answer > 0 and answer <= len(values):
                break
            else:
                print(Red("Invalid choice"))
        except:
            print(Red("Invalid choice"))
    return values[answer-1]