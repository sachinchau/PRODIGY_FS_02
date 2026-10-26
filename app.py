from flask_wtf.csrf import CSRFProtect
from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from extensions import db
from auth import auth_bp, login_required
app = Flask(__name__)
app.config.from_object(Config)

csrf = CSRFProtect(app)
db.init_app(app)
app.register_blueprint(auth_bp)
from models import Admin, Employee



@app.route("/")
@login_required
def home():
    total_employees = Employee.query.count()

    total_departments = db.session.query(
        db.func.count(db.func.distinct(Employee.department))
    ).scalar()
    department_counts = (
        db.session.query(
            Employee.department,
            db.func.count(Employee.id).label("employee_count")
        )
        .group_by(Employee.department)
        .order_by(Employee.department)
        .all()
    )


    recent_employees = Employee.query.order_by(
        Employee.id.desc()
    ).limit(5).all()

    return render_template(
        "index.html",
        total_employees=total_employees,
        total_departments=total_departments,
        recent_employees=recent_employees,
        department_counts=department_counts
    )

@app.route("/employees")
@login_required
def employees():
    search = request.args.get("search", "").strip()

    query = Employee.query

    if search:
        query = query.filter(
            db.or_(
                Employee.name.ilike(f"%{search}%"),
                Employee.email.ilike(f"%{search}%"),
                Employee.department.ilike(f"%{search}%")
            )
        )

    employee_list = query.order_by(Employee.id.desc()).all()

    return render_template(
        "employees.html",
        employees=employee_list,
        search=search
    )


@app.route("/employees/add", methods=["GET", "POST"])
@login_required
def add_employee():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        department = request.form.get("department", "").strip()
        designation = request.form.get("designation", "").strip()
        salary_text = request.form.get("salary", "").strip()

        if not all([name, email, phone, department, designation, salary_text]):
            flash("All fields are required.", "danger")
            return redirect(url_for("add_employee"))

        try:
            salary = float(salary_text)
            if salary < 0:
                raise ValueError
        except ValueError:
            flash("Please enter a valid, non-negative salary.", "danger")
            return redirect(url_for("add_employee"))

        if Employee.query.filter_by(email=email).first():
            flash("An employee with this email already exists.", "danger")
            return redirect(url_for("add_employee"))

        employee = Employee(
            name=name,
            email=email,
            phone=phone,
            department=department,
            designation=designation,
            salary=salary,
        )

        db.session.add(employee)
        db.session.commit()

        flash("Employee added successfully!", "success")
        return redirect(url_for("employees"))

    return render_template("add_employee.html")


@app.route("/db-test")
def db_test():
    try:
        with db.engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        return "MySQL connection successful!"
    except Exception:
        app.logger.exception("Database connection failed")
        return "Database connection failed. Check server and configuration.", 500


with app.app_context():
    db.create_all()


@app.route("/employees/edit/<int:employee_id>", methods=["GET", "POST"])
@login_required
def edit_employee(employee_id):
    employee = db.session.get(Employee, employee_id)

    if employee is None:
        flash("Employee not found.", "danger")
        return redirect(url_for("employees"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        department = request.form.get("department", "").strip()
        designation = request.form.get("designation", "").strip()
        salary_text = request.form.get("salary", "").strip()

        if not all([name, email, phone, department, designation, salary_text]):
            flash("All fields are required.", "danger")
            return render_template("edit_employee.html", employee=employee)

        try:
            from decimal import Decimal
            salary = Decimal(salary_text)
            if not salary.is_finite() or salary < 0:
                raise ValueError
        except (ValueError, ArithmeticError):
            flash("Please enter a valid, non-negative salary.", "danger")
            return render_template("edit_employee.html", employee=employee)

        existing_email = Employee.query.filter(
            Employee.email == email,
            Employee.id != employee_id
        ).first()

        if existing_email:
            flash("Another employee already uses this email.", "danger")
            return render_template("edit_employee.html", employee=employee)

        employee.name = name
        employee.email = email
        employee.phone = phone
        employee.department = department
        employee.designation = designation
        employee.salary = salary

        db.session.commit()
        flash("Employee updated successfully!", "success")
        return redirect(url_for("employees"))

    return render_template("edit_employee.html", employee=employee)


@app.route("/employees/delete/<int:employee_id>", methods=["POST"])
@login_required
def delete_employee(employee_id):
    employee = db.session.get(Employee, employee_id)

    if employee is None:
        flash("Employee not found.", "danger")
        return redirect(url_for("employees"))

    db.session.delete(employee)
    db.session.commit()

    flash("Employee deleted successfully!", "success")
    return redirect(url_for("employees"))


if __name__ == "__main__":
    app.run(debug=True)
