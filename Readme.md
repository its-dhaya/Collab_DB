//table creation
create table_name
//example
create users

//data insertion 
insert table_name {"key":"value"}
//example
insert users {"name":"John", "age":"30","email":"john@example.com"}


//get data
select table_name
select table_name field_name
//example
select users
select users name

//deleting a specific field 
delete field_name from table_name where condition
//example
delete name from users where age=30

//void which similar to drop
void from table_name where condition
void from table_name 
void  table_name
//example
void from users where name = John
void from users
void users

//update 
update table_name set field_name = new_value where condition
//example
update users set name = "Bob" where age=30

