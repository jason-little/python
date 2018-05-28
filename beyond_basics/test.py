txt = "Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim. Donec pede justo, fringilla vel, aliquet nec, vulputate eget, arcu. Etiam ultricies nisi vel augue. Curabitur ullamcorper ultricies nisi. Nam eget dui. Etiam rhoncus. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient python, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim. Donec pede justo, fringilla vel, aliquet nec, vulputate eget, arcu. Etiam ultricies nisi vel augue. Curabitur ullamcorper ultricies nisi. Nam eget dui. Etiam rhoncus. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis, baxa quouq. axa la consequat massa quis enim. Donec pede justo, fringilla vel, aliquet nec, vulputate eget, arcu. Etiam ultricies nisi vel augue. Curabitur ullamcorper ultricies nisi. Proin at neque et tellus ultricies consequat. Duis vitae mi commodo, suscipit nunc vel, porta tellus. In eu volutpat sapien. Mauris dignissim velit eget diam tristique, nec egestas magna maximus. Pellentesque python, lorem a eleifend vehicula, arcu urna facilisis odio, maximus maximus massa nisl sed sapien. Quisque nisi nunc, dignissim ut malesuada non, fringilla vitae sem. Nunc turpis quam, rutrum at egestas ut, pretium tincidunt est. Praesent imperdiet mauris eu felis lobortis vehicula. Sed dictum lorem at rutrum rhoncus. Suspendisse sit amet ex ac eros python cursus. Duis pretium rutrum lacus, sit amet vulputate ipsum condimentum vel. Vivamus lacus ipsum, python in justo quis, blandit condimentum velit esed semper posuere leo, elementum tristique leo euismod quis."

import string
alphabets=string.ascii_lowercase
#txt2 = txt.replace(".", "")
#txt3 = txt2.replace(",", "")
txt_list=txt.split()
P=0
C=0
for i in txt_list:
    if '.' in i and len(i) == 4:
        P += 1
    elif ',' in i and len(i) ==4:
        C += 1
print(str(C) + str(P))
#print(txt_list[10] + txt_list[269])
#ln=len(txt_list)
#li=[]
#for i in str(ln):
#    li.append(alphabets[int(i)])
#li="".join(li)
#print(li)
