const fs = require("fs");

const dbFile = "storage.json";

// Read database
function readDatabase() {
  return JSON.parse(fs.readFileSync(dbFile, "utf8"));
}

// Write database
function writeDatabase(data) {
  fs.writeFileSync(dbFile, JSON.stringify(data, null, 2));
}

// Function to parse and execute custom SQL-like queries
function parseCommand(query) {
  const data = readDatabase();
  const tokens = query.split(" ");

  switch (tokens[0].toLowerCase()) {
    case "create": {
      // Create database (simply initialize an empty object)
      if (!fs.existsSync(dbFile)) writeDatabase({ tables: {} });
      return "Database created successfully!";
    }

    case "make": {
      // Create table
      const tableName = tokens[1];
      if (!data.tables[tableName]) {
        data.tables[tableName] = [];
        writeDatabase(data);
        return `Table ${tableName} created successfully!`;
      }
      return `Table ${tableName} already exists.`;
    }

    case "include": {
      // Insert data into table
      const tableName = tokens[1];
      const jsonString = query.substring(query.indexOf("["));
      try {
        const newData = JSON.parse(jsonString);
        if (!Array.isArray(newData)) return "Invalid insert format!";
        data.tables[tableName] = [...(data.tables[tableName] || []), ...newData];
        writeDatabase(data);
        return `Data inserted into ${tableName}!`;
      } catch (error) {
        return "Error parsing JSON data!";
      }
    }

    case "select": {
      // Fetch data from table
      const tableName = tokens[1];
      return data.tables[tableName] || "Table not found!";
    }

    case "count": {
      // Count records in a table
      const tableName = tokens[1];
      return data.tables[tableName] ? data.tables[tableName].length : "Table not found!";
    }

    case "exclude": {
      // Delete table
      const tableName = tokens[1];
      if (data.tables[tableName]) {
        delete data.tables[tableName];
        writeDatabase(data);
        return `Table ${tableName} deleted!`;
      }
      return `Table ${tableName} does not exist.`;
    }

    default:
      return "Invalid command!";
  }
}


function parseCommand(command) {
  const data = JSON.parse(fs.readFileSync(dbFile, "utf8"));

  if (command.startsWith("select students")) {
    return data.students || [];
  }

  if (command.startsWith("include students")) {
    const jsonData = command.match(/\[(.*?)\]/)[0];  // Fixed regex
    const newStudents = JSON.parse(jsonData);
    data.students.push(...newStudents);
    fs.writeFileSync(dbFile, JSON.stringify(data, null, 2));
    return newStudents;
  }

  if (command.startsWith("exclude from students where id=")) {
    const id = parseInt(command.split("=")[1]);
    data.students = data.students.filter(student => student.id !== id);
    fs.writeFileSync(dbFile, JSON.stringify(data, null, 2));
    return { message: "Student deleted" };
  }

  if (command.startsWith("update students set")) {
    const [_, field, value, condition] = command.match(/set (\w+) = "(.*?)" where id=(\d+)/);
    const student = data.students.find(s => s.id === parseInt(condition));
    if (student) {
      student[field] = value;
      fs.writeFileSync(dbFile, JSON.stringify(data, null, 2));
      return student;
    }
    return { message: "Student not found" };
  }

  return [];
}

module.exports = { parseCommand };


module.exports = { parseCommand };
