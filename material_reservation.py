import math

class MaterialReservation:
    def __init__(self, connection):
        self.connection = connection

    def get_available_stock(self, material_id, dimensions, length):
        result = self.connection.execute("""
        SELECT id, material_id, m3_quantity, dimensions, length
        FROM warehouse
        WHERE material_id = ? AND dimensions = ? AND length = ? AND m3_quantity > 0     
    """, (material_id, dimensions, length)).fetchone()  
        return result

    def has_enough_stock(self, material_id, dimensions, length, requested_m3):
        available_stock = self.get_available_stock(material_id, dimensions, length)
        if available_stock and ( available_stock[2] >= requested_m3 or math.isclose(available_stock[2], requested_m3,rel_tol=0, abs_tol=1e-9)):
            return True
        return False

    def reserve_materials(self, material_id, dimensions, length, requested_m3, order_item_id):
        has_stock = self.has_enough_stock(material_id, dimensions, length, requested_m3)
        if not has_stock:
            raise Exception("Nie ma wystarczającej ilości materiału w magazynie do rezerwacji.")
        stock_entry = self.get_available_stock(material_id, dimensions, length)
        if stock_entry:
            result1 = self.connection.execute("""
                UPDATE warehouse
                SET m3_quantity = MAX(m3_quantity - ?, 0)
                WHERE id = ? AND m3_quantity + 0.000000001 >= ?
            """, (requested_m3, stock_entry[0], requested_m3))

            if result1.rowcount > 0:
                self.connection.execute("""
                    INSERT INTO material_reservations (order_item_id, warehouse_id, m3_quantity)
                    VALUES (?, ?, ?)
                """, (order_item_id, stock_entry[0], requested_m3))
                return True
            else:
                raise Exception("Nie udało się zarezerwować materiału w magazynie.")
            
        

    def release_materials(self, order_id):
        order_status = self.connection.execute("SELECT status FROM orders WHERE orders.id = ? ", (order_id,)).fetchone()
        if order_status is None:
            raise Exception("Nie znaleziono zamówienia o podanym ID.")

        if order_status[0] == "CANCELLED":

            result1 = self.connection.execute("""
            SELECT mr.id, mr.warehouse_id, mr.m3_quantity
            FROM material_reservations as mr
            INNER JOIN order_items AS oi ON mr.order_item_id = oi.id
            WHERE oi.order_id = ? """, (order_id,)).fetchall()

            for reservation in result1:
                reservation_to_release = reservation[0]
                warehouse_id = reservation[1]
                m3_quantity = reservation[2]

                result2 = self.connection.execute("""
                UPDATE warehouse
                SET m3_quantity = m3_quantity + ?
                WHERE id = ?""", (m3_quantity, warehouse_id))
                if result2.rowcount > 0:
                    self.connection.execute("""
                    DELETE FROM material_reservations
                    WHERE id = ?""", (reservation_to_release,))
                else:
                    raise Exception("Nie udało się zwolnić materiału w magazynie.")
            return True
            
        elif order_status[0] == "COMPLETED":
            self.connection.execute("""
            DELETE FROM material_reservations
            WHERE order_item_id IN (
                SELECT id FROM order_items WHERE order_id = ?
            )""", (order_id,))
            return True
        else:
            raise Exception("Zamówienie nie jest w stanie, który pozwala na zwolnienie materiałów.")

    def has_reservations(self, order_id):
        result = self.connection.execute("""
        SELECT COUNT(*) FROM material_reservations
        WHERE order_item_id IN (
            SELECT id FROM order_items WHERE order_id = ?
        )""", (order_id,)).fetchone()
        return result[0] > 0


        
        

        