from datetime import date, datetime

CRA = {
    date(2024, 1, 1): {
        # Pay periods
        "pay_periods": 12,

        # CPP
        "cpp_rate": 0.0595,
        "cpp_basic_exemption": 3500.00,
        "monthly_cpp_exemption": 291.66,
        "cpp_first_additional_rate": 0.0100,
        "max_annual_base_cpp": 3217.50,
        "base_cpp_rate": 0.0495,
        "cpp_ympe": 68500.00,

        # CPP2
        "cpp2_rate": 0.0400,
        "cpp2_max_annual_contribution": 188.00,
        "cpp2_yampe": 73200.00,

        # Employment Insurance
        "ei_rate": 0.0166,
        "ei_max_annual_insurable_earnings": 63200.00,
        "max_annual_ei": 1049.12,

        # Federal
        "federal_claim_amount": 15705.00,
        "canada_employment_amount": 1433.00,

        # (upper income limit, tax rate, constant)
        "federal_brackets": [
            (55867, 0.15, 0.00),
            (111733, 0.205, 3072.69),
            (173205, 0.26, 9217.99),
            (246752, 0.29, 14414.14),
            (float("inf"), 0.33, 24284.22),
        ],

        # Alberta
        "alberta_claim_amount": 21885.00,

        # K5P
        "k5p_threshold": 0.00,
        "k5p_rate": 0.00,

        # (upper income limit, tax rate, constant)
        "alberta_brackets": [
            (148269, 0.10, 0.00),
            (177922, 0.12, 2965.00),
            (237230, 0.13, 4745.00),
            (355845, 0.14, 7117.00),
            (float("inf"), 0.15, 10675.00),
        ],
    },
    
    date(2025, 1, 1): {
        # Pay periods
        "pay_periods": 12,

        # CPP
        "cpp_rate": 0.0595,
        "cpp_basic_exemption": 3500.00,
        "monthly_cpp_exemption": 291.66,
        "cpp_first_additional_rate": 0.0100,
        "max_annual_base_cpp": 3356.10,
        "base_cpp_rate": 0.0495,
        "cpp_ympe": 71300.00,

        # CPP2
        "cpp2_rate": 0.0400,
        "cpp2_max_annual_contribution": 396.00,
        "cpp2_yampe": 81200.00,

        # Employment Insurance
        "ei_rate": 0.0164,
        "ei_max_annual_insurable_earnings": 65700.00,
        "max_annual_ei": 1077.48,

        # Federal
        "federal_claim_amount": 16129.00,
        "canada_employment_amount": 1471.00,

        # (upper income limit, tax rate, constant)
        "federal_brackets": [
            (57375, 0.15, 0.00),
            (114750, 0.205, 3156.00),
            (177882, 0.26, 9467.00),
            (253414, 0.29, 14803.00),
            (float("inf"), 0.33, 24940.00),
        ],

        # Alberta
        "alberta_claim_amount": 22323.00,

        # K5P
        "k5p_threshold": 0.00,
        "k5p_rate": 0.00,

        # (upper income limit, tax rate, constant)
        "alberta_brackets": [
            (151234, 0.10, 0.00),
            (181481, 0.12, 3025.00),
            (241974, 0.13, 4839.00),
            (362961, 0.14, 7259.00),
            (float("inf"), 0.15, 10889.00),
        ],
    }
}


def get_cra_parameters(payroll_date):
    """Return the CRA parameters effective on the payroll date."""

    effective_dates = sorted(CRA.keys())

    applicable_dates = [
        effective_date
        for effective_date in effective_dates
        if effective_date <= payroll_date
    ]

    if not applicable_dates:
        raise ValueError(
            f"No CRA parameters available for {payroll_date}."
        )

    latest_effective_date = applicable_dates[-1]

    return CRA[latest_effective_date]

def calculate_cpp(amount, cpp_rate, monthly_cpp_exemption):
    """Calculate CPP for a single pay period."""
    return max(
        0,
        (amount - monthly_cpp_exemption) * cpp_rate
    )

def calculate_cpp2(payroll, payroll_date, cra):
    """Calculate CPP2 for the current pay period."""

    completed_months = payroll_date.month - 1

    ytd_pensionable_earnings = (
        completed_months * payroll
    )

    total_pensionable_earnings = (
        ytd_pensionable_earnings + payroll
    )

    cpp2_earnings = min(
        max(
            0,
            total_pensionable_earnings - cra["cpp_ympe"]
        ),
        cra["cpp2_yampe"] - cra["cpp_ympe"]
    )

    cpp2 = cpp2_earnings * cra["cpp2_rate"]

    return cpp2

def calculate_payroll(
    payroll_before_employer_cpp,
    cpp_rate,
    monthly_cpp_exemption
):
    """Calculate payroll after reserving the employer's CPP contribution."""
    estimated_employer_cpp = calculate_cpp(
        payroll_before_employer_cpp,
        cpp_rate,
        monthly_cpp_exemption
    )

    return payroll_before_employer_cpp - estimated_employer_cpp
    
def get_tax_bracket(annual_taxable_income, brackets):
    """Return the tax rate and bracket constant for the given income."""
    for upper_limit, rate, constant in brackets:
        if annual_taxable_income <= upper_limit:
            return rate, constant

    raise ValueError("No tax bracket found")

def calculate_ei(amount, ei_rate, max_annual_ei, pay_periods):
    """Calculate EI premiums for a single pay period."""

    annual_insurable_earnings = min(
        pay_periods * amount,
        cra["ei_max_annual_insurable_earnings"]
    )
    
    annual_ei = min(
        ei_rate * annual_insurable_earnings,
        max_annual_ei
    )

    return annual_ei / pay_periods
    
def calculate_tax_inputs(payroll, employee_cpp, employee_cpp2):
    """Calculate annual values shared by federal and Alberta tax calculations."""
    pay_periods = cra["pay_periods"]

    # Deductible additional CPP contribution
    cpp_first_additional_rate = cra["cpp_first_additional_rate"]

    f5 = (
        employee_cpp
        * (cpp_first_additional_rate / cra["cpp_rate"])
        + employee_cpp2
    )

    # Annual taxable income
    annual_taxable_income = pay_periods * (payroll - f5)

    # Federal tax credit for base CPP contributions
    base_cpp_rate = cra["base_cpp_rate"]
    cpp_basic_exemption = cra["cpp_basic_exemption"]
    max_annual_base_cpp = cra["max_annual_base_cpp"]

    annual_base_cpp = min(
        base_cpp_rate * (
            (pay_periods * payroll) - cpp_basic_exemption
        ),
        max_annual_base_cpp
    )
    
    # Annual EI premiums used for the federal and Alberta tax credits.
    ei_rate = cra["ei_rate"]
    max_annual_ei = cra["max_annual_ei"]

    annual_ei = min(
        ei_rate * (pay_periods * payroll),
        max_annual_ei
    )

    return annual_taxable_income, annual_base_cpp, annual_ei, f5
    
def calculate_federal_tax(
    annual_taxable_income,
    annual_base_cpp,
    annual_ei,
    payroll
):
    """Calculate federal income tax for one pay period."""
    pay_periods = cra["pay_periods"]

    # T4127: Select the federal tax bracket for annual taxable income.
    federal_rate, federal_constant = get_tax_bracket(
        annual_taxable_income,
        cra["federal_brackets"]
    )
    
    print(f"Federal rate:          {federal_rate:.3%}")
    print(f"Federal constant:      ${federal_constant:,.2f}")

    # T4127 factor K1:
    # Federal non-refundable personal tax credit
    federal_claim_amount = cra["federal_claim_amount"]
    federal_lowest_tax_rate = cra["federal_brackets"][0][1]

    k1 = federal_lowest_tax_rate * federal_claim_amount
    
    print(f"Federal K1:            ${k1:,.2f}")

    # T4127 factor K2:
    # Federal tax credit for base CPP contributions and EI premiums.
    k2 = federal_lowest_tax_rate * (
        annual_base_cpp + annual_ei
    )
    
    print(f"Federal K2:             ${k2:,.2f}")

    # T4127 factor K4:
    # Federal Canada Employment Amount tax credit
    canada_employment_amount = cra["canada_employment_amount"]

    k4 = min(
        federal_lowest_tax_rate * (pay_periods * payroll),
        federal_lowest_tax_rate * canada_employment_amount
    )
    
    print(f"Federal k4:             ${k4:,.2f}")

    k3 = 0.00

    # Calculate basic federal tax (T3).
    t3 = (
        federal_rate * annual_taxable_income
        - federal_constant
        - k1
        - k2
        - k3
        - k4
    )

    print(f"Federal t3:             ${t3:,.2f}")

    lcf = 0.00

    # Calculate annual federal tax payable (T1).
    t1 = max(0, t3 - (pay_periods * lcf))
    
    print(f"Federal t1:             ${t1:,.2f}")

    federal_tax = t1 / pay_periods

    return federal_tax

def calculate_alberta_tax(
    annual_taxable_income,
    annual_base_cpp,
    annual_ei
):
    """Calculate Alberta income tax for one pay period."""
    pay_periods = cra["pay_periods"]

    # T4127: Select the Alberta tax bracket.
    alberta_rate, alberta_constant = get_tax_bracket(
        annual_taxable_income,
        cra["alberta_brackets"]
    )
    
    print(f"Alberta rate:          {alberta_rate:.3%}")
    print(f"Alberta constant:      ${alberta_constant:,.2f}")

    # T4127 factor K1P:
    # Alberta non-refundable personal tax credit.
    alberta_claim_amount = cra["alberta_claim_amount"]
    alberta_lowest_tax_rate = cra["alberta_brackets"][0][1]

    k1p = alberta_lowest_tax_rate * alberta_claim_amount
    
    print(f"Alberta K1P:            ${k1p:,.2f}")

    # T4127 factor K2P:
    # Alberta tax credit for base CPP contributions and EI premiums.
    k2p = alberta_lowest_tax_rate * (
        annual_base_cpp + annual_ei
    )
    
    print(f"Alberta K2P:             ${k2p:,.2f}")

    k3p = 0.00

    # Calculate basic Alberta tax (T4).
    t4 = (
        alberta_rate * annual_taxable_income
        - alberta_constant
        - k1p
        - k2p
        - k3p
    )
    
    print(f"Alberta t4:             ${t4:,.2f}")
    
    # Annual Alberta tax payable (T2).
    t2 = t4

    # Convert annual Alberta tax to the current pay period.
    alberta_tax = t2 / pay_periods

    return alberta_tax


# Begin program

# get date
while True:
    date_input = input(
        f"Enter payroll date (YYYY-MM-DD) [default: {date.today()}]: "
    ).strip()

    if not date_input:
        payroll_date = date.today()
        break

    try:
        payroll_date = datetime.strptime(
            date_input,
            "%Y-%m-%d"
        ).date()
        break
    except ValueError:
        print("Invalid date. Please enter the date as YYYY-MM-DD.")

# Select the CRA parameters for the year being calculated.
cra = get_cra_parameters(payroll_date)

# get total
while True:
    total_input = input("Enter total including GST: $").strip()

    try:
        total = float(total_input)

        if total < 0:
            print("Total cannot be negative.")
            continue

        break
    except ValueError:
        print("Invalid amount. Please enter a number.")
    
print(f"Payroll date: {payroll_date}")

# Calculate the GST portion of the amount received.
gst = total / 21

# Amount remaining after GST.
earned = total - gst

# Get the CPP parameters for the selected CRA year.
cpp_rate = cra["cpp_rate"]
monthly_cpp_exemption = cra["monthly_cpp_exemption"]

# Calculate payroll after reserving the employer's CPP contribution.
payroll = calculate_payroll(
    earned,
    cpp_rate,
    monthly_cpp_exemption
)

# Calculate employee CPP on the resulting payroll.
employee_cpp = calculate_cpp(
    payroll,
    cpp_rate,
    monthly_cpp_exemption
)

# Employer CPP is equal to the employee CPP contribution.
employer_cpp = employee_cpp

# Calculate employee CPP2 on the resulting payroll.
employee_cpp2 = calculate_cpp2(payroll, payroll_date, cra)

# Employer CPP2 is equal to the employee CPP2 contribution.
employer_cpp2 = employee_cpp2

# Get EI constants
ei_rate = cra["ei_rate"]
max_annual_ei = cra["max_annual_ei"]

# Calculate emplyee EI
employee_ei = calculate_ei(
    payroll,
    ei_rate,
    max_annual_ei,
    cra["pay_periods"]
)

# Calculate annual values required by both federal and Alberta tax.
annual_taxable_income, annual_base_cpp, annual_ei, f5 = calculate_tax_inputs(
    payroll,
    employee_cpp,
    employee_cpp2
)

print(f"F5:                    ${f5:,.2f}")

# Calculate federal and Alberta income tax.
federal_tax = calculate_federal_tax(annual_taxable_income, annual_base_cpp, annual_ei, payroll)
alberta_tax = calculate_alberta_tax(annual_taxable_income, annual_base_cpp, annual_ei)

# Combine federal and Alberta tax.
total_tax = federal_tax + alberta_tax


# Output

# Optional diagnostic output for validating individual T4127 calculations.
print(f"Total:  ${total:,.2f}")
print(f"GST:    ${gst:,.2f}")
print(f"Earned: ${earned:,.2f}")
#print(f"Estimated employer CPP: ${estimated_employer_cpp:,.2f}")
print(f"Payroll:                ${payroll:,.2f}")
print(f"Employee CPP:           ${employee_cpp:,.2f}")
print(f"Employer CPP:           ${employer_cpp:,.2f}")
print(f"Employee CPP2:          ${employee_cpp2:,.2f}")
#print(f"Additional CPP (F5):     ${f5:,.2f}")
print(f"Annual taxable income A: ${annual_taxable_income:,.2f}")
#print(f"Federal rate (R):         {federal_rate:.1%}")
#print(f"Federal constant (K):     ${federal_constant:,.2f}")
#print(f"Federal claim amount (TC): ${federal_claim_amount:,.2f}")
#print(f"Federal tax credit (K1):   ${k1:,.2f}")
print(f"Annual base CPP:          ${annual_base_cpp:,.2f}")
print(f"Annual EI:              ${annual_ei:,.2f}")
#print(f"Federal CPP credit (K2):  ${k2:,.2f}")
#print(f"Canada Employment Amount: ${canada_employment_amount:,.2f}")
#print(f"Federal employment credit (K4): ${k4:,.2f}")
#print(f"Basic federal tax (T3):   ${t3:,.2f}")
#print(f"Annual federal tax (T1):  ${t1:,.2f}")
#print(f"Alberta rate (V):          {alberta_rate:.1%}")
#print(f"Alberta constant (KP):     ${alberta_constant:,.2f}")
#print(f"Alberta claim amount (TCP): ${alberta_claim_amount:,.2f}")
#print(f"Alberta tax credit (K1P):   ${k1p:,.2f}")
#print(f"Alberta CPP credit (K2P): ${k2p:,.2f}")
#print(f"Basic Alberta tax (T4):   ${t4:,.2f}")
#print(f"Annual Alberta tax (T2):  ${t2:,.2f}")
print(f"Federal tax for pay period: ${federal_tax:,.2f}")
print(f"Alberta tax for pay period: ${alberta_tax:,.2f}")
print(f"Total tax for pay period:   ${total_tax:,.2f}")