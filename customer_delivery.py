from database import Database
from fuel import Fuel
import sqlite3
class Customers:
    def __init__(self, connection):
        self.connection = connection

    def add_customers(self, customer_type, first_name, last_name, company_name, nip, phone, email):
        try:
            if customer_type == "PERSON":
                result = self.connection.execute("""
                INSERT INTO customers (customer_type, first_name, last_name, phone, email)
                VALUES ('PERSON', ?, ?, ?, ?)""", (first_name, last_name, phone, email))
            elif customer_type == "COMPANY":
                result = self.connection.execute("""
                INSERT INTO customers (customer_type, company_name, nip, phone, email)
                VALUES ('COMPANY', ?, ?, ?, ?)""", (company_name, nip, phone, email))
            else:
                raise ValueError("Niepoprawny typ klienta. Wybierz 'PERSON' lub 'COMPANY'.")
            self.connection.commit()
        except sqlite3.IntegrityError as error:
            self.connection.rollback()
            if error.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
                return None
            raise
        
        
        if result.rowcount > 0:
            return result.lastrowid
        else:
             raise Exception("Nie udało się dodać klienta do bazy danych")
    def delete_customers(self, id_to_delete: int):
        with self.connection:
            result = self.connection.execute("DELETE FROM customers WHERE id = ?", (id_to_delete,))
        return result.rowcount > 0

    def get_customers(self, search_term=None):
        search_term = (search_term or "").strip()
        pattern = f"%{search_term}%"
        return self.connection.execute("""
            SELECT id, customer_type, first_name, last_name, company_name, nip, phone, email
            FROM customers
            WHERE (COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')) LIKE ?
               OR company_name LIKE ?
               OR nip LIKE ?
        """, (pattern, pattern, pattern)).fetchall()

    def display_customers(self, search_term=None):
        results = self.get_customers(search_term)
        customers = []
        for customer in results:
            if customer[1] == "PERSON":
                description = (
                    f"ID: {customer[0]}, Typ klienta: {customer[1]}, "
                    f"Imię: {customer[2]}, Nazwisko: {customer[3]}"
                )
            elif customer[1] == "COMPANY":
                description = (
                    f"ID: {customer[0]}, Typ klienta: {customer[1]}, "
                    f"Nazwa firmy: {customer[4]}, NIP: {customer[5]}"
                )
            else:
                continue
            description += f", Telefon: {customer[6]}, Email: {customer[7]}"
            print(description)
            customers.append((customer[0], description))

        return customers


class CustomerManager:
    def __init__(self, validator, customers):
        self.validator = validator
        self.customers = customers
    def add_customer(self):
        types = ["PERSON", "COMPANY"]
        customer_type = self.validator.select_option_from_list(types, "Wybierz typ klienta: ")
        

        if customer_type == "PERSON":
            first_name = self.validator.read_input("Podaj imię klienta: ").strip()
            last_name = self.validator.read_input("Podaj nazwisko klienta: ").strip()
            while not first_name or not last_name:
                print("Imię i nazwisko nie mogą być puste. Spróbuj ponownie.")
                first_name = self.validator.read_input("Podaj imię klienta: ").strip()
                last_name = self.validator.read_input("Podaj nazwisko klienta: ").strip()
            
            phone = self.validator.read_input("Podaj numer telefonu klienta: ")
            email = self.validator.read_input("Podaj adres email klienta: ")
            customer_id = self.customers.add_customers(customer_type, first_name, last_name, None, None, phone, email)
            
        elif customer_type == "COMPANY":
            company_name = self.validator.read_input("Podaj nazwę firmy: ").strip()
            nip = self.validator.read_input("Podaj NIP firmy: ").strip()
            while not company_name or not nip:
                print("Nazwa firmy i NIP nie mogą być puste. Spróbuj ponownie.")
                company_name = self.validator.read_input("Podaj nazwę firmy: ").strip()
                nip = self.validator.read_input("Podaj NIP firmy: ").strip()
            
            phone = self.validator.read_input("Podaj numer telefonu firmy: ")
            email = self.validator.read_input("Podaj adres email firmy: ")
            customer_id = self.customers.add_customers(customer_type, None, None, company_name, nip, phone, email)

        if customer_id is None:
            print("Ten NIP jest już w bazie.")
            return None

        print("Klient został poprawnie dodany do bazy danych.")
        return customer_id
            
    def display_customers(self):
        search_term = self.validator.read_input(
            "Wpisz imię, nazwisko, nazwę firmy lub NIP (Enter wyświetla wszystkich): "
        )
        results = self.customers.display_customers(search_term)
        if not results:
            print("Nie znaleziono klientów.")
        return results

    def delete_customer(self):
        results = self.display_customers()
        if not results:
            return

        id_to_delete = self.validator.get_valid_number("Podaj ID klienta do usunięcia: ", int, 1)
        if not any(id_to_delete == customer[0] for customer in results):
            print("Tego klienta nie ma na liście wyników.")
            return


        try:
            deleted = self.customers.delete_customers(id_to_delete)
        except sqlite3.IntegrityError as error:
            if error.sqlite_errorcode != sqlite3.SQLITE_CONSTRAINT_FOREIGNKEY:
                raise
            print("Nie można usunąć klienta, ponieważ jest powiązany z zamówieniem.")
            return

        if deleted:
            print(f"Klient o ID {id_to_delete} został usunięty.")
        else:
            print(f"Nie znaleziono klienta o ID {id_to_delete}.")

class DeliveryLocations:
    def __init__(self, connection, fuel):
        self.connection = connection
        self.fuel = fuel

    def get_customer_name(self):
        results = self.connection.execute("""
        SELECT customers.id, customers.customer_type, customers.first_name, customers.last_name, customers.company_name FROM customers """).fetchall()
        customers = []
        for entry in results:
            if entry[1] == "PERSON":
                description = (f"Id:{entry[0]} Imie:{entry[2]} Nazwisko:{entry[3]}")
            elif entry[1] == "COMPANY":
                description = (f"Id:{entry[0]} Nazwa firmy:{entry[4]}")
            customers.append((entry[0], description))
        return customers
    def get_dist(self, address):
        distance = self.fuel.get_route_info(address)

        return distance
    
    def add_delivery_locations(self, customer_id, name, address):
        distance = self.get_dist(address)
        if distance is None:
            return None
        result =self.connection.execute("""
            INSERT INTO delivery_locations (customer_id, name, address, distance)
            VALUES (?, ?, ?, ?)""", (customer_id, name, address, distance))
        self.connection.commit()

        if result.rowcount > 0:
            return result.lastrowid
        else:
            raise Exception("Nie udało się dodać miejsca dostawy do bazy danych")

    def delete_delivery_locations(self, id_to_delete: int):
        with self.connection:
            result = self.connection.execute("DELETE FROM delivery_locations WHERE id = ?", (id_to_delete,))
        return result.rowcount > 0

    def get_delivery_locations(self, search_term=None):
        search_term = (search_term or "").strip()
        pattern = f"%{search_term}%"
        return self.connection.execute("""
            SELECT d.id, c.first_name, c.last_name, c.company_name, d.name, d.address
            FROM delivery_locations AS d
            JOIN customers AS c ON c.id = d.customer_id
            WHERE COALESCE(d.address, '') LIKE ? OR d.name LIKE ?
        """, (pattern, pattern)).fetchall()

    def display_delivery_locations(self, search_term=None):
        results = self.get_delivery_locations(search_term)
        locations = []
        for location in results:
            if location[1] is not None and location[2] is not None:
                customer_name = f"{location[1]} {location[2]}"
            elif location[3] is not None:
                customer_name = location[3]
            else:
                continue
            description = (
                f"ID: {location[0]}, Klient: {customer_name}, "
                f"Nazwa miejsca dostawy: {location[4]}, Adres: {location[5]}"
            )
            print(description)
            locations.append((location[0], description))

        return locations


class DeliveryLocationManager:
    def __init__(self, validator, delivery_locations):
        self.validator = validator
        self.delivery_locations = delivery_locations

    def add_delivery_location(self, customer_id=None):
        
        if customer_id is None:
            customer_ids_list = self.delivery_locations.get_customer_name()
            if not customer_ids_list:
                print("Brak klientów w bazie danych. Najpierw dodaj klienta.")
                return
            for description in customer_ids_list:
                print(description[1])
            customer_id = self.validator.get_valid_number("Podaj ID klienta: ", int, 1)
            if not any(customer_id == customer[0] for customer in customer_ids_list):
                print("Nieprawidłowy ID klienta.")
                return
        name = self.validator.read_input("Podaj nazwę miejsca dostawy: ")
        address = self.validator.read_input("Podaj adres miejsca dostawy: ")
        delivery_location_id = self.delivery_locations.add_delivery_locations(customer_id, name, address)
        if delivery_location_id is None:
            print("Nie udało się dodać miejsca dostawy. Sprawdź adres i połączenie z internetem.")
            return None

        print("Miejsce dostawy zostało poprawnie dodane do bazy danych")
        return delivery_location_id

    def display_delivery_locations(self):
        search_term = self.validator.read_input("Wpisz adres lub nazwę miejsca dostawy (Enter wyświetla wszystkie): ")
        results = self.delivery_locations.display_delivery_locations(search_term)
        if not results:
            print("Nie znaleziono miejsc dostawy.")
        return results

    def delete_delivery_location(self):
        results = self.display_delivery_locations()
        if not results:
            return

        id_to_delete = self.validator.get_valid_number("Podaj ID miejsca dostawy do usunięcia: ", int, 1)
        if not any(id_to_delete == location[0] for location in results):
            print("Tego miejsca dostawy nie ma na liście wyników.")
            return

        try:
            deleted = self.delivery_locations.delete_delivery_locations(id_to_delete)
        except sqlite3.IntegrityError as error:
            if error.sqlite_errorcode != sqlite3.SQLITE_CONSTRAINT_FOREIGNKEY:
                raise
            print("Nie można usunąć miejsca dostawy, ponieważ jest powiązane z zamówieniem.")
            return

        if deleted:
            print(f"Miejsce dostawy o ID {id_to_delete} zostało usunięte.")
        else:
            print(f"Nie znaleziono miejsca dostawy o ID {id_to_delete}.")
