import os
import json
import shutil

DB_FOLDER = "databases"
os.makedirs(DB_FOLDER, exist_ok=True)

current_db = None
current_db_file = None
_id_counter = {}

def load_db(db_name):
    global current_db, current_db_file
    db_path = os.path.join(DB_FOLDER, db_name, "storage.json")
    
    if os.path.exists(db_path):
        with open(db_path, "r") as f:
            try:
                current_db = json.load(f)
            except json.JSONDecodeError:
                current_db = {}
    else:
        current_db = {}
    
    current_db_file = db_path
    update_id_counter()  # Update the ID counter after loading the DB

def update_id_counter():
    """Update the _id_counter for each table in the current database."""
    global _id_counter
    
    if current_db is not None:
        for table_name, records in current_db.items():
            if records:
                # Get the maximum ID from the records, default to 0 if none
                max_id = max(record.get("id", 0) for record in records)
            else:
                max_id = 0
            _id_counter[table_name] = max_id

def save_db():
    """Save the database to the current database's JSON file."""
    if current_db_file:
        with open(current_db_file, "w") as f:
            json.dump(current_db, f, indent=4)

def process_command(command):
    global current_db, current_db_file
    
    tokens = command.strip().split()

    # Remove the semicolon if present at the end of the command
    if tokens[-1].endswith(";"):
        tokens[-1] = tokens[-1][:-1]

    if not tokens:
        return "Invalid command."

    action = tokens[0].lower()
    
    if action == "show" and len(tokens) == 2 and tokens[1].lower() == "databases":
        # List all the databases present in the DB_FOLDER
        databases = [db for db in os.listdir(DB_FOLDER) if os.path.isdir(os.path.join(DB_FOLDER, db))]
        if databases:
            return "Databases: " + ", ".join(databases)
        else:
            return "No databases found."
    
    elif action == "create" and len(tokens) == 3 and tokens[1].lower() == "database":
        db_name = tokens[2]
        db_path = os.path.join(DB_FOLDER, db_name)
        
        if os.path.exists(db_path):
            return f"Database '{db_name}' already exists."
        
        os.makedirs(db_path)
        # Initialize an empty storage file for the new database
        with open(os.path.join(db_path, "storage.json"), "w") as f:
            json.dump({}, f)
        
        return f"Database '{db_name}' created successfully"
    
    elif action == "use" and len(tokens) == 2:
        db_name = tokens[1]
        db_path = os.path.join(DB_FOLDER, db_name)
        
        if not os.path.exists(db_path):
            return f"Database '{db_name}' does not exist."
        else:
            load_db(db_name)
            return f"Using database '{db_name}'"
        
    elif action == "exit" and len(tokens) == 2:
        db_name = tokens[1]

        if current_db is None:
            return "No database is currently in use."

        db_path = os.path.join(DB_FOLDER, db_name)
        if not os.path.exists(db_path):
            return f"Database '{db_name}' does not exist."

        if current_db_file and db_name in current_db_file:
            save_db()  # Save changes before exiting
            current_db_file = None
            current_db = None
            return f"Exited from database '{db_name}'. You can now use another database."
        else:
            return f"Database '{db_name}' is not currently in use."
        

    elif action == "remove" and len(tokens) == 2:
        db_name = tokens[1]
        db_path = os.path.join(DB_FOLDER, db_name)
        
        if not os.path.exists(db_path):
            return f"Database '{db_name}' does not exist."
        
        shutil.rmtree(db_path)  # Deletes the entire database folder
        if current_db_file and db_name in current_db_file:
            current_db_file = None
            current_db = None

        return f"Database '{db_name}' deleted successfully."


    elif action == "make" and len(tokens) >= 2:
        if current_db is None:
            return "No database selected. Use 'USE database_name' to select a database."

        table_name = tokens[1]
        if table_name in current_db:
            return f"Table '{table_name}' already exists."
        current_db[table_name] = []
        _id_counter[table_name] = 0  # Initialize ID counter for the table
        save_db()
        return f"Table '{table_name}' created successfully."

    elif action == "insert":
        if len(tokens) < 3:
            return "Syntax error. Usage: INSERT table_name {data};"
        table_name = tokens[1]
        data = command.split("{", 1)[-1].split("}", 1)[0]
        try:
            if not data:
                return "Empty data provided."
            data = data.strip()
            record = json.loads(f"{{{data}}}")

            if table_name in current_db:
                # Auto-increment ID
                _id_counter[table_name] += 1
                record["id"] = _id_counter[table_name]

                current_db[table_name].append(record)
                save_db()
                return f"Record inserted into '{table_name}' with ID {record['id']}."
            else:
                return f"Table '{table_name}' does not exist."
        except json.JSONDecodeError as e:
            return f"Invalid JSON format: {e}"

    elif action == "select":
        if len(tokens) < 2:
            return "Syntax error. Usage: SELECT table_name [field_name] WHERE condition [ORDER BY field_name ASC/DESC] [GROUP BY field_name];"

        table_name = tokens[1]
        fields = []
        condition_clause = None
        order_field = None
        order_direction = "asc"
        group_field = None
        where_index = len(tokens)
        
        # Check for WHERE condition
        if "where" in tokens:
            where_index = tokens.index("where")
            condition_clause = " ".join(tokens[where_index + 1:])
            fields = tokens[2:where_index] if len(tokens) > 2 and tokens[2] != "where" else []
        else:
            fields = tokens[2:] if len(tokens) > 2 else []

        # Handle ORDER BY clause
        if "order" in tokens and "by" in tokens:
            order_index = tokens.index("order")
            order_field = tokens[order_index + 2]
            if len(tokens) > order_index + 3 and tokens[order_index + 3].lower() in ["asc", "desc"]:
                order_direction = tokens[order_index + 3].lower()

        # Handle GROUP BY clause
        if "group" in tokens and "by" in tokens:
            group_index = tokens.index("group")
            group_field = tokens[group_index + 2]

        fields = [field.strip() for field in " ".join(fields).split(",") if field.strip()]

        if table_name in current_db:
            result = current_db[table_name]

            # Apply WHERE condition if exists
            if condition_clause:
                condition_field, condition_value = condition_clause.split("=")
                condition_field = condition_field.strip()
                condition_value = condition_value.strip().strip("'")
                result = [record for record in result if record.get(condition_field) == condition_value]

            # Apply GROUP BY if exists
            if group_field:
                grouped = {}
                for record in result:
                    group_key = record.get(group_field)
                    if group_key is not None:
                        if group_key not in grouped:
                            grouped[group_key] = []
                        grouped[group_key].append(record)
                result = [{"group": group_key, "records": records} for group_key, records in grouped.items()]

            # Apply ORDER BY if exists
            if order_field:
                result = sorted(result, key=lambda x: x.get(order_field, ""), reverse=(order_direction == "desc"))

            if fields:
                result = [{field: record.get(field) for field in fields} for record in result]

            return json.dumps(result, indent=4) if result else "No records matched the condition."
        else:
            return f"Table '{table_name}' does not exist."
    

    elif action == "update":
        if "set" not in tokens or "where" not in tokens:
            return "Syntax error. Usage: UPDATE table_name SET field_name = new_value WHERE condition;"

        table_name = tokens[1]
        set_index = tokens.index("set")
        where_index = tokens.index("where")

        # Extract the SET clause and WHERE clause
        set_clause = " ".join(tokens[set_index + 1:where_index])
        where_clause = " ".join(tokens[where_index + 1:])

        if "=" not in set_clause or "=" not in where_clause:
            return "Syntax error in SET or WHERE clause."

        # Split the SET clause into field_name and new_value
        field_name, new_value = set_clause.split("=")
        field_name = field_name.strip()
        new_value = new_value.strip().strip('"')

        # Split the WHERE clause into condition_field and condition_value
        condition_field, condition_value = where_clause.split("=")
        condition_field = condition_field.strip()
        condition_value = condition_value.strip().strip('"')

        if table_name in current_db:
            modified_count = 0  # Initialize the counter
            for record in current_db[table_name]:
                if str(record.get(condition_field)) == condition_value:
                    # Convert the new value to the correct type
                    if isinstance(record.get(field_name), int):
                        new_value = int(new_value)
                    elif isinstance(record.get(field_name), float):
                        new_value = float(new_value)

                    # Update the record
                    record[field_name] = new_value
                    modified_count += 1  # Increment the counter

            if modified_count > 0:
                save_db()
                return f"{modified_count} record(s) updated in '{table_name}'."
            else:
                return "No records matched the condition."
        else:
            return f"Table '{table_name}' does not exist."



    elif action == "void":
        if len(tokens) < 2:
            return "Syntax error. Usage: VOID table_name; OR VOID FROM table_name WHERE condition;"

        # Case 1: Void the entire table (Delete table itself)
        if len(tokens) == 2:
            table_name = tokens[1]

            # Ensure table exists
            if table_name not in current_db:
                return f"Table '{table_name}' does not exist."

            # Delete the entire table
            del current_db[table_name]
            save_db()
            return f"Table '{table_name}' has been voided."

        # Case 2: Void records from a table (Must include 'FROM')
        if tokens[1].lower() == "from":
            if len(tokens) < 3:
                return "Syntax error. Usage: VOID FROM table_name; OR VOID FROM table_name WHERE condition;"

            table_name = tokens[2]

            # Ensure table exists
            if table_name not in current_db:
                return f"Table '{table_name}' does not exist."

            # Case 2a: Void all records from the table (No WHERE Clause)
            if len(tokens) == 3:
                current_db[table_name] = []  # Clear all records but keep the table
                save_db()
                return f"All records voided from '{table_name}'."

            # Case 2b: Void specific records using WHERE condition
            if len(tokens) > 3 and tokens[3].lower() == "where":
                if len(tokens) < 6 or "=" not in " ".join(tokens[4:]):
                    return "Syntax error in WHERE clause. Expected format: VOID FROM table_name WHERE field = value;"

                # Extract condition clause
                condition_clause = " ".join(tokens[4:])
                condition_field, condition_value = condition_clause.split("=")
                condition_field = condition_field.strip()
                condition_value = condition_value.strip().strip("'")

                # Convert condition value type if necessary
                for record in current_db[table_name]:
                    if condition_field in record:
                        if isinstance(record[condition_field], int):
                            condition_value = int(condition_value)
                        elif isinstance(record[condition_field], float):
                            condition_value = float(condition_value)
                        break  # Stop checking after the first record

                # Remove matching records
                original_count = len(current_db[table_name])
                current_db[table_name] = [record for record in current_db[table_name] if record.get(condition_field) != condition_value]

                # Save and return response
                if len(current_db[table_name]) < original_count:
                    save_db()
                    return f"Voided {original_count - len(current_db[table_name])} record(s) from '{table_name}'."
                else:
                    return "No matching records found."

        return "Syntax error. Use: VOID table_name; OR VOID FROM table_name WHERE condition;"


    elif action == "delete":
        if len(tokens) < 4 or tokens[2] != "from" or "where" not in tokens:
            return "Syntax error. Usage: DELETE [field_name] FROM table_name WHERE condition;"

        table_name = tokens[3]
        where_index = tokens.index("where")
        condition_clause = " ".join(tokens[where_index + 1:])

        # Extract condition field and value
        if "=" not in condition_clause:
            return "Syntax error in WHERE clause."
        
        condition_field, condition_value = condition_clause.split("=")
        condition_field = condition_field.strip()
        condition_value = condition_value.strip().strip("'")

        if table_name in current_db:
            modified_count = 0  # Count of records modified

            # Type conversion for numerical fields
            for record in current_db[table_name]:
                if condition_field in record:
                    if isinstance(record[condition_field], int):
                        condition_value = int(condition_value)
                    elif isinstance(record[condition_field], float):
                        condition_value = float(condition_value)
                    break  # Stop checking after the first record

            # Check if it's deleting the entire record or a specific field
            if len(tokens) > 4:
                field_name = tokens[1]  # Specific field to delete
                # Deleting specific field
                for record in current_db[table_name]:
                    if record.get(condition_field) == condition_value:
                        if field_name in record:
                            del record[field_name]
                            modified_count += 1
            else:
                # Deleting the entire record
                for record in current_db[table_name]:
                    if record.get(condition_field) == condition_value:
                        current_db[table_name].remove(record)
                        modified_count += 1
                        break  # Stop after removing the first matching record
                    
    elif action == "count":
        if len(tokens) < 2:
            return "Syntax error. Usage: COUNT table_name;"

        table_name = tokens[1]

        if table_name in current_db:
            record_count = len(current_db[table_name])
            return f"Table '{table_name}' contains {record_count} record(s)."
        else:
            return f"Table '{table_name}' does not exist."
        
    elif action == "show" and len(tokens) == 2 and tokens[1].lower() == "tables":
    # Show all table names
        if current_db:
            table_names = list(current_db.keys())
            return f"Tables: {', '.join(table_names)}"
        else:
            return "No tables found."

            # Save if any records were modified
    if modified_count > 0:
        save_db()
        if len(tokens) > 4:
            return f"Deleted field '{field_name}' from {modified_count} record(s) in '{table_name}'."
        else:
            return f"Deleted {modified_count} record(s) from '{table_name}'."
    else:
        return "No records matched the condition or field not found."

def cli():
    print("SimpleDB CLI. Type 'exit' to quit.")
    while True:
        command = input("db> ")
        if command.lower() == "exit":
            break
        response = process_command(command)
        print(response)

if __name__ == "__main__":
    cli()