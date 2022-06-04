import base64
import os

val = input("Enter desired password: ")
confirm = input("Confirm desired password: ")

while  val != confirm:
    print('Passwords are different please try again.')
    val = input("Enter desired password: ")
    confirm = input("Confirm desired password: ")

encoded = base64.b64encode(val.encode("utf-8"))


save_path = os.getcwd() + '\\Database\\secret'

with open(save_path, 'wb') as f:
    f.write(encoded)

print('encoded password has been saved here {0}'.format(save_path), 'KEEP THIS A SECRET!!!', sep='\n')