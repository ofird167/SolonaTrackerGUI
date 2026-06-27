import flet as ft

try:
    print("1. Testing Border class constructor:")
    b1 = ft.Border(right=ft.BorderSide(1, "#29292e"))
    print("Border constructor ok:", b1)
    
    print("2. Testing ft.Border.all static method:")
    b2 = ft.Border.all(width=1, color="#29292e")
    print("ft.Border.all ok:", b2)
    
    print("3. Testing only borders via Border constructor:")
    b3 = ft.Border(right=ft.BorderSide(1, "#29292e"))
    print("Border only ok:", b3)
    
    print("All tests completed!")
except Exception as e:
    print("Error encountered:", e)
