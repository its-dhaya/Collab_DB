const express = require("express");
const cors = require("cors");
const bodyParser = require("body-parser");
const { parseCommand } = require("./db"); // Assuming this executes custom queries

const app = express();
const PORT = 5000;

// Middleware
app.use(cors());
app.use(bodyParser.json());

// 📌 1. Get All Students
app.get("/students", (req, res) => {
  try {
    const result = parseCommand("select students");
    res.json(result);
  } catch (error) {
    res.status(500).json({ message: "Error fetching students", error });
  }
});

// 📌 2. Get Student by ID
app.get("/students/:id", (req, res) => {
  try {
    const id = parseInt(req.params.id);
    const result = parseCommand("select students");
    const student = result.find((s) => s.id === id);
    student ? res.json(student) : res.status(404).json({ message: "Student not found" });
  } catch (error) {
    res.status(500).json({ message: "Error fetching student", error });
  }
});

// 📌 3. Add a New Student
app.post("/students", (req, res) => {
  try {
    const newStudent = { id: Date.now(), ...req.body };
    // Make sure the insert query is correctly formatted
    parseCommand(`include students [${JSON.stringify(newStudent)}]`);
    res.json(newStudent);
  } catch (error) {
    res.status(500).json({ message: "Error adding student", error });
  }
});

// 📌 4. Update a Student
app.put("/students/:id", (req, res) => {
  try {
    const id = parseInt(req.params.id);
    const updates = req.body;

    // Update each field individually
    Object.keys(updates).forEach((key) => {
      parseCommand(`update students set ${key} = "${updates[key]}" where id=${id}`);
    });

    const updatedStudent = parseCommand("select students").find((s) => s.id === id);
    res.json(updatedStudent);
  } catch (error) {
    res.status(500).json({ message: "Error updating student", error });
  }
});

// 📌 5. Delete a Student
app.delete("/students/:id", (req, res) => {
  try {
    const id = parseInt(req.params.id);
    // Ensure the delete query is properly formatted
    parseCommand(`exclude from students where id=${id}`);
    res.json({ message: "Student deleted" });
  } catch (error) {
    res.status(500).json({ message: "Error deleting student", error });
  }
});

// Start Server
app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`));
