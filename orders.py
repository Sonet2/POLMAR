from database import Database
from fuel import Fuel
from wood_catalog import WoodCatalog
from datetime import datetime
from blueprints import Blueprints
from truss_manager import TrussManager
from customer_delivery import CustomerManager, DeliveryLocationManager
from material_reservation import MaterialReservation

class Order:
    def __init__(self, connection, catalog, fuel):
        self.connection = connection
        self.catalog = catalog
        self.fuel = fuel

    def get_customer_id(self):
        results = self.connection.execute("""
        SELECT customers.id, customers.customer_type, customers.first_name, customers.last_name, customers.company_name 
        FROM customers """).fetchall()
        customers = []
        for entry in results:
            if entry[1] == "PERSON":
                description = (f"Id:{entry[0]} Imie:{entry[2]} Nazwisko:{entry[3]}")
            elif entry[1] == "COMPANY":
                description = (f"Id:{entry[0]} Nazwa firmy:{entry[4]}")
            customers.append((entry[0], description))
        return customers

    def get_delivery_locations(self, customer_id):
        results = self.connection.execute("""
            SELECT delivery_locations.id, delivery_locations.name, delivery_locations.address
            FROM delivery_locations
            WHERE delivery_locations.customer_id = ?""", (customer_id,)).fetchall()
        delivery_locations = []
        for entry in results:
            description = f"Id:{entry[0]} Nazwa:{entry[1]} Adres:{entry[2]}"
            delivery_locations.append((entry[0], description))
        return delivery_locations

    def get_delivery_distance(self, delivery_location_id):
        results = self.connection.execute("""
            SELECT distance 
            FROM delivery_locations 
            WHERE id = ?""", (delivery_location_id,)).fetchone()
        return results[0] if results else None

    def set_created_at(self):
        from datetime import datetime
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return created_at
    def get_order_items(self, order_id):
        return self.connection.execute("""
            SELECT m.category, i.m3_quantity, i.length, i.dimensions,
                i.line_total_grosze, 
            COALESCE(SUM(mr.m3_quantity), 0) AS reserved_m3
            FROM order_items AS i
            JOIN materials AS m ON m.id = i.material_id
            LEFT JOIN material_reservations AS mr ON mr.order_item_id = i.id
            WHERE i.order_id = ?
            GROUP BY i.id
            ORDER BY i.id
        """, (order_id,)).fetchall()
  
    def create_orders(self, customer_id, delivery_location_id, order_type, status, created_at, delivery_date, fuel_cost_grosze, fuel_consumption):
        
        result = self.connection.execute("""
        INSERT INTO orders (customer_id, delivery_location_id, order_type, status, created_at, delivery_date, fuel_cost_grosze, fuel_consumption)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (customer_id, delivery_location_id, order_type, status, created_at, delivery_date, fuel_cost_grosze, fuel_consumption))
        return result.lastrowid 

    def add_order_items(self, order_id, material_id, m3_quantity, length, dimensions, price_per_m3_grosze):
        result = self.connection.execute("""
        INSERT INTO order_items (order_id, material_id, m3_quantity, length, dimensions, price_per_m3_grosze, line_total_grosze)
        VALUES(?,?,?,?,?,?,0)""", (order_id, material_id, m3_quantity, length, dimensions, price_per_m3_grosze))
        return result.lastrowid
   
    def display_orders(self, search_term):
        pattern = f"%{search_term}%"
        results = self.connection.execute("""
        SELECT o.id,
        CASE
            WHEN c.customer_type = 'COMPANY' THEN c.company_name
            ELSE c.first_name || ' ' || c.last_name
        END AS customer_name,
        d.address AS delivery_address,
        o.order_type, o.status, o.created_at, o.delivery_date,
        COALESCE(o.fuel_cost_grosze, 0), o.fuel_consumption, o.total_order_price_grosze
        FROM orders AS o
        JOIN customers AS c ON c.id = o.customer_id
        JOIN delivery_locations AS d ON d.id = o.delivery_location_id
        WHERE (c.first_name || ' ' || c.last_name) LIKE ? OR c.company_name LIKE ?
        """, (pattern, pattern)).fetchall()
        orders = []
        for order in results:
            description = f"Id zamówienia: {order[0]}, Klient: {order[1]}, Miejsce dostawy: {order[2]}, Typ zamówienia: {order[3]}, Status: {order[4]}, Data utworzenia: {order[5]}, Data dostawy: {order[6]}, Koszt paliwa: {order[7] / 100:.2f} zł, Zużycie paliwa (l): {order[8]}, Do zapłaty: {order[9] / 100:.2f} zł"
            print(description)
            for category, quantity, length, dimensions, total, reserved_m3 in self.get_order_items(order[0]):
                print(f"  - {category}, {quantity} m³, dł. {length} m, "
                    f"wymiary {dimensions} , zarezerwowane: {reserved_m3} m³, razem {total / 100:.2f} zł")
            orders.append((order[0], description))

        return orders

    def delete_orders(self, order_id):
        result = self.connection.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        self.connection.commit()
        if result.rowcount > 0:
            return True
        else:
            return False

    def change_orders_status(self,order_id, new_status):
        result = self.connection.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        if result.rowcount > 0:
            return True
        else:
            return False
        
    def get_order_status(self, order_id):
        result = self.connection.execute("SELECT status FROM orders WHERE id = ?", (order_id,)).fetchone()
        if result:
            return result[0]
        else:
            return None


class OrderManager:
    def __init__(self, validator, order, catalog, truss_manager, blueprints, fuel, customer_manager, delivery_location_manager, material_reservation):
        self.validator = validator
        self.order = order
        self.catalog = catalog
        self.truss_manager = truss_manager
        self.blueprints = blueprints
        self.fuel = fuel
        self.customer_manager = customer_manager
        self.delivery_location_manager = delivery_location_manager
        self.material_reservation = material_reservation

    def collect_one_item(self):
        return self.blueprints.wood_selection()
    
    def print_items(self, items):
        for index, item in enumerate(items, start=1):
            category, subcategory, specie, price, m3_quantity, length, dimensions = item
            print(f"Id {index}: Kategoria: {category}, Podkategoria: {subcategory}, Gatunek: {specie}, Cena za m3: {(price / 100):.2f} zł, Ilość w m3: {m3_quantity}, Długość: {length}, Wymiary: {dimensions}")
                                            
    def ask_next_step(self):
        choice = self.validator.select_option_from_list(["Dodaj kolejną pozycję", "Usuń ostatnią pozycje", "Potwierdź zamówienie", "Anuluj  zamówienie"], "Wybierz opcję: ")
        if choice == "Dodaj kolejną pozycję":
            return "add"
        elif choice == "Usuń ostatnią pozycje":
            return "remove"
        elif choice == "Potwierdź zamówienie":
            return "confirm"
        elif choice == "Anuluj  zamówienie":
            return "cancel"

    def collect_loose_items(self):
        items = [self.collect_one_item()]
        while True:
            self.print_items(items)
            choice = self.ask_next_step()
            if choice == "add":
                items.append(self.collect_one_item())
            elif choice == "remove":
                items.pop()
                if not items:
                    items.append(self.collect_one_item())
            elif choice == "confirm":
                return items
            elif choice == "cancel":
                return None  

    def collect_truss_items(self):
        while True:
            truss = self.truss_manager.collect_truss()
            items = self.truss_manager.build_items(truss)
            self.print_items(items)
            choice = self.validator.select_option_from_list(["Potwierdź zamówienie", "Anuluj zamówienie", "Wpisz więźbe od nowa"], "Wybierz opcję: ")
            if choice == "Potwierdź zamówienie":
                return items
            elif choice == "Anuluj zamówienie":
                return None
            

    def create_order(self):
        customer_ids_list = self.order.get_customer_id()
        if not customer_ids_list:
            print("Brak klientów w bazie danych. Najpierw dodaj klienta.")
        
        for description in customer_ids_list:
            print(description[1])

        print("Klienta nie ma na liscie? Wpisz w ID cyfrę \"0\" aby dodac nowego klienta.")
        customer_id = self.validator.get_valid_number("Podaj ID klienta: ", int, 0)

        if customer_id == 0:
            customer_id = self.customer_manager.add_customer()

            if customer_id is None:
                return
            
        elif not any(customer_id == customer[0] for customer in customer_ids_list):
            print("Nieprawidłowy ID klienta.")
            return
        
        delivery_locations = self.order.get_delivery_locations(customer_id)
        if not delivery_locations:
            print("Brak miejsc dostawy dla tego klienta. Najpierw dodaj miejsce dostawy.")
        

        if len(delivery_locations) == 1:
            delivery_location_id = delivery_locations[0][0]
            print(f"Wybrano jedyne miejsce dostawy: {delivery_locations[0][1]}")
        else:
            for location in delivery_locations:
                print(location[1])

            print("Miejsca dostawy nie ma na liscie? Wpisz w ID cyfrę \"0\" aby dodac nowe miejsce dostawy.")
            delivery_location_id = self.validator.get_valid_number("Podaj ID miejsca dostawy: ", int, 0)
            if delivery_location_id == 0:
                delivery_location_id = self.delivery_location_manager.add_delivery_location(customer_id)
    
                if delivery_location_id is None:
                    return
            elif not any(delivery_location_id == location[0] for location in delivery_locations):
                print("Nieprawidłowy ID miejsca dostawy.")
                return
            
        to_reserve = []
        enough = []
        not_enough = []

        oder_types = ["Materiał luźny", "Więźba dachowa"]
        for index, order_type in enumerate(oder_types, start=1):
            print(f"{index}. {order_type}")
        order_type = self.validator.get_valid_number("Wybierz typ zamówienia (1-2): ", int, 1, 2)
        if order_type == 1:
            order_type = "LOOSE"
            collected_items = self.collect_loose_items()
        else:
            order_type = "TRUSS"
            collected_items = self.collect_truss_items()
        if collected_items is None:
            print("Zamówienie anulowane.")
            return
        
        collected_items = self.merge_items(collected_items)

        for item in collected_items:
            category, subcategory, specie, price, m3_quantity, length, dimensions = item
            material_id = self.catalog.get_position_id(category, subcategory, specie)
            if self.material_reservation.has_enough_stock(material_id[0], dimensions, length, m3_quantity):
                enough.append(item)
            else:
                not_enough.append(item)

        print("Dla następujących pozycji materiału jest wystarczająca ilość w magazynie:")
        for item in enough:
            category, subcategory, specie, price, m3_quantity, length, dimensions = item
            print(f"Kategoria: {category}, Podkategoria: {subcategory}, Gatunek: {specie}, Ilość w m3: {m3_quantity}, Długość: {length}, Wymiary: {dimensions}")
        
        print("Nie ma wystarczającej ilości materiału w magazynie do rezerwacji dla następujących pozycji:")
        for item in not_enough:
            category, subcategory, specie, price, m3_quantity, length, dimensions = item
            print(f"Kategoria: {category}, Podkategoria: {subcategory}, Gatunek: {specie}, Ilość w m3: {m3_quantity}, Długość: {length}, Wymiary: {dimensions}")

        
        while True:
            print("Wybierz co chcesz zrobić z tymi pozycjami:")
            print("1. Pobierz wszystkie z magazynu")
            print("2. Pobierz tylko niektóre z magazynu")
            print("3. Zakończ zbieranie pozycji bez pobierania materiału z magazynu")
            choice = self.validator.get_valid_number("Wybierz opcję (1-3): ", int, 1, 3)
            if choice == 1:
                for item in enough:
                    to_reserve.append(item)
                break
            elif choice == 2:
                while True:
                    self.print_items(enough)
                    item_index = self.validator.get_valid_number("Wybierz ID pozycji do pobrania z magazynu (0 aby zakończyć): ", int, 0, len(enough))
                    if item_index == 0:
                        break
                    selected_item = enough[item_index - 1]
                    to_reserve.append(selected_item)
                    enough.remove(selected_item)
                    if not enough:
                        print("Nie ma już pozycji do pobrania z magazynu.")
                        break
                break
            elif choice == 3:
                break  
        
        status = "IN_PROGRESS"
        created_at = self.order.set_created_at()
        delivery_date = self.validator.get_valid_date("Podaj datę dostawy (RRRR-MM-DD): ")
        distance = self.order.get_delivery_distance(delivery_location_id)
        if distance is None:
            print("Nie można obliczyć kosztów paliwa, brak danych o odległości.")
            return
        fuel_cost_grosze, fuel_consumption = self.fuel.calculate_from_distance(distance)
        try:
            order_id = self.order.create_orders(customer_id, delivery_location_id, order_type, status, created_at, delivery_date, fuel_cost_grosze, fuel_consumption)
            for item in collected_items:
                category, subcategory, specie, price, m3_quantity, length, dimensions = item
                material_ids = self.catalog.get_position_id(category, subcategory, specie)
                if not material_ids:
                    raise ValueError(f"Nie znaleziono materiału w katalogu: {category}, {subcategory}, {specie}")
                material_id = material_ids  [0]
                order_item_id = self.order.add_order_items(order_id, material_id, m3_quantity, length, dimensions, price)
                if item in to_reserve:
                    self.material_reservation.reserve_materials(material_id, dimensions, length, m3_quantity, order_item_id)
                    to_reserve.remove(item)
            self.order.connection.commit()
        except Exception:
            self.order.connection.rollback()
            raise

    def display_order(self):
        search_term = self.validator.read_input(
            "Wpisz imię, nazwisko lub nazwę firmy (Enter wyświetla wszystkie zamówienia): ").strip()
        res= self.order.display_orders(search_term)
        if not res:
            print("Brak zamówień do wyświetlenia.")
        return res


    def delete_order(self):
        results = self.display_order()
        if not results:
            print("Brak zamówień do usunięcia.")
            return
        
        id_to_delete = self.validator.get_valid_number("Wprowadź ID ZAMÓWNIENIA do usunięcia: ", int, 1)
        if not any(id_to_delete == order[0] for order in results):
            print("Nieprawidłowy ID zamówienia.")
            return

        if self.material_reservation.has_reservations(id_to_delete):
            print("Nie można usunąć zamówienia, ponieważ istnieją zarezerwowane materiały w magazynie. Najpierw anuluj zamówienie, aby zwrócić materiał do magazynu.")
            return
           
        if self.order.delete_orders(id_to_delete):
            print(f"Zamówienie o ID {id_to_delete} zostało usunięte.")
        else:
            print(f"Nie znaleziono zamówienia o ID {id_to_delete}.")

    def change_order_status(self):
        results = self.display_order()
        if not results:
            print("Brak zamówień do zmiany statusu.")
            return
        
        id_to_change = self.validator.get_valid_number("Wprowadź ID ZAMÓWNIENIA do zmiany statusu: ", int, 1)
        if not any(id_to_change == order[0] for order in results):
            print("Nieprawidłowy ID zamówienia.")
            return

        current_status = self.order.get_order_status(id_to_change)
        if current_status is None:
            print("Nie znaleziono zamówienia o podanym ID.")
            return
        if current_status in ("CANCELLED", "COMPLETED"):
            print(f"Nie można zmienić statusu zamówienia o ID {id_to_change}, ponieważ jest ono już w stanie '{current_status}'.")
            return
        
        new_status = self.validator.select_option_from_list([ "COMPLETED", "CANCELLED"], "Wybierz nowy status zamówienia: ")
       
        try:
            changed = self.order.change_orders_status(id_to_change, new_status)

            if changed:
                if new_status in ("CANCELLED", "COMPLETED"):
                    self.material_reservation.release_materials(id_to_change)

                self.order.connection.commit()
                print(f"Status zamówienia o ID {id_to_change} został zmieniony na {new_status}.")
            else:
                print(f"Nie znaleziono zamówienia o ID {id_to_change}.")

        except Exception:
            self.order.connection.rollback()
            raise
    def merge_items(self, items):
        merged_items = {}
        for item in items:
            key = (item[0], item[1], item[2], item[5], item[6])
            if key in merged_items:
                merged_items[key][4] += item[4]  
            else:
                merged_items[key] = list(item)
        return list(merged_items.values())