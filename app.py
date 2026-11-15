from warehouse_management import WarehouseManager, Warehouse
from wood_catalog import WoodCatalog
from validators import Validator
from database import Database
from orders import Order, OrderManager
from fuel import Fuel
from customer_delivery import Customers, CustomerManager,DeliveryLocations, DeliveryLocationManager
from validators import Validator
from blueprints import Blueprints
from truss_manager import TrussManager


class Menu:
    def __init__(self, warehouse, warehouse_manager, order_manager,customer_manager,delivery_locations_manager):
        self.warehouse = warehouse
        self.warehouse_manager = warehouse_manager
        self.order_manager = order_manager
        self.customer_manager = customer_manager
        self.delivery_locations_manager = delivery_locations_manager
        

    def display_menu(self):
        print("Wybierz opcję:")
        print("0. Wyjście z programu")
        print("1. Obsługa Magazynu")
        print("2. Zamówienie dla klienta")
        print("3. Obsługa klientów i lokalizacji dostaw")
        output = input("Wprowadź numer opcji: ")
        return output
    
    def get_user_choice(self, output):
        if output == "1":
            self.warehouse_option()
        elif output == "2":
            self.order_option()
        elif output == "3":
            self.customer_option()
        elif output == "0":
            print("Zamknięcie programu.")
        else:
            print("Nieprawidłowa opcja. Spróbuj ponownie.")

    def warehouse_option(self):
        
        while True:
            print("Wybrano opcję 1: Obsługa Magazynu")
            print("Wybierz działanie:")
            print("0. Powrót do menu głównego")
            print("1. Dodaj materiał do magazynu")
            print("2. Usuń materiał z magazynu")
            print("3. Wyświetl zawartość magazynu")
            warehouse_choice = input("Wprowadź numer opcji: ")
            
            if warehouse_choice == "1":
                self.warehouse_manager.add_to_warehouse()
            elif warehouse_choice == "2":
                self.warehouse_manager.delete_from_warehouse()
            elif warehouse_choice == "3":
                self.warehouse.display_warehouse()
            elif warehouse_choice == "0":
                break
            else:
                print("Nieprawidłowa opcja. Spróbuj ponownie.")

        
    def order_option(self):
        while True:
            print("Wybrano opcję 2: Zamówienie dla klienta")
            print("0. Powrót do menu głównego")
            print("1. Utwórz nowe zamówienie")
            print("2. Wyświetl zamówienia")
            print("3. Usuń zamówienie")
            order_choice = input("Wprowadź numer opcji: ")
            if order_choice == "1":
                self.order_manager.create_order()
            elif order_choice == "2":
                while True:
                    print("1. Wyświetl wszystkie zamówienia")
                    print("2. Wyświetl zamowienia dla klienta indywidualnego")
                    print("3. Wyświetl zamowienia dla klienta biznesowego")
                    print("4. Usuń zamówienie")
                    print("0. Powrót do menu głównego")
                    sub_choice = input("Wprowadź numer opcji: ")
                    if sub_choice == "1":
                        self.order_manager.display_order(search_term="")
                    elif sub_choice == "2":
                        self.order_manager.display_order()
                    elif sub_choice == "3":
                        self.order_manager.display_order()
                    elif sub_choice == "4":
                        self.order_manager.delete_order()
                    elif sub_choice == "0":
                        return
                    else:
                        print("Nieprawidłowa opcja. Spróbuj ponownie.")
            elif order_choice == "3":
                self.order_manager.delete_order()
            elif order_choice == "0":
                break
            else:
                print("Nieprawidłowa opcja. Spróbuj ponownie.")

    def customer_option(self):
        while True:
            print("Wybrano opcję 3: Obsługa klientów i lokalizacji dostaw")
            print("0. Powrót do menu głównego")
            print("1. Dodaj klienta")
            print("2. Wyświetl klientów")
            print("3. Usuń klienta")
            print("4. Dodaj miejsce dostawy")
            print("5. Wyświetl miejsca dostawy")
            print("6. Usuń miejsce dostawy")
            customer_choice = input("Wprowadź numer opcji: ")
            if customer_choice == "1":
                self.customer_manager.add_customer()
            elif customer_choice == "2":
                self.customer_manager.display_customers()
            elif customer_choice == "3":
                self.customer_manager.delete_customer()
            elif customer_choice == "4":
                self.delivery_locations_manager.add_delivery_location()
            elif customer_choice == "5":
                self.delivery_locations_manager.display_delivery_locations()
            elif customer_choice == "6":
                self.delivery_locations_manager.delete_delivery_location()
            elif customer_choice == "0":
                break
            else:
                print("Nieprawidłowa opcja. Spróbuj ponownie.")
            

if __name__ == "__main__":
    database = Database(None)
    connection = database.connect()
    fuel = Fuel()
    validator = Validator()
    catalog = WoodCatalog(connection)
    warehouse = Warehouse(connection, catalog)
    warehouse_manager = WarehouseManager(catalog, validator, warehouse)
    truss_manager = TrussManager(validator, catalog)
    blueprints = Blueprints(validator, catalog)
    customers = Customers(connection)
    customer_manager = CustomerManager(validator, customers)
    delivery_locations = DeliveryLocations(connection, fuel)
    delivery_locations_manager = DeliveryLocationManager(validator, delivery_locations)
    order = Order(connection, catalog, fuel)
    order_manager = OrderManager(validator, order, catalog, truss_manager, blueprints, fuel, customer_manager, delivery_locations_manager)
    

    menu = Menu(warehouse, warehouse_manager, order_manager, customer_manager, delivery_locations_manager)
    while True:
        output = menu.display_menu()
        menu.get_user_choice(output)
        if output == "0":
            break
        
