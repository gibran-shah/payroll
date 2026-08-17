CRA = {
    2024: {
        # Number of pay periods in the year.
        "pay_periods": 12,

        # CPP constants.
        "cpp_rate": 0.0595,
        "cpp_basic_exemption": 3500.00,
        "monthly_cpp_exemption": 291.66,
        "cpp_first_additional_rate": 0.0100,
        "max_annual_base_cpp": 3217.50,
        "base_cpp_rate": 0.0495,

        # Federal tax constants.
        "federal_claim_amount": 15705.00,
        "canada_employment_amount": 1433.00,
        
        # Federal tax brackets:
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
        
        # Alberta tax brackets:
        # (upper income limit, tax rate, constant)
        "alberta_brackets": [
            (148269, 0.10, 0.00),
            (177922, 0.12, 2965.00),
            (237230, 0.13, 4745.00),
            (355845, 0.14, 7117.00),
            (float("inf"), 0.15, 10675.00),
        ],
    }
}

# Select the CRA parameters for the year being calculated.
cra = CRA[2024]



def calculate_cpp(amount, cpp_rate, monthly_cpp_exemption):
    """Calculate CPP for a single pay period."""
    return max(
        0,
        (amount - monthly_cpp_exemption) * cpp_rate
    )


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
    
def calculate_tax_inputs(payroll, employee_cpp, cra):
    """Calculate annual values shared by federal and Alberta tax calculations."""
    pay_periods = cra["pay_periods"]

    # Deductible additional CPP contribution
    cpp_first_additional_rate = cra["cpp_first_additional_rate"]

    f5 = employee_cpp * (
        cpp_first_additional_rate / cra["cpp_rate"]
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

    return annual_taxable_income, annual_base_cpp
    
def calculate_federal_tax(
    annual_taxable_income,
    annual_base_cpp,
    payroll
):
    """Calculate federal income tax for one pay period."""
    pay_periods = cra["pay_periods"]

    # T4127: Select the federal tax bracket for annual taxable income.
    federal_rate, federal_constant = get_tax_bracket(
        annual_taxable_income,
        cra["federal_brackets"]
    )

    # T4127 factor K1:
    # Federal non-refundable personal tax credit
    federal_claim_amount = cra["federal_claim_amount"]
    federal_lowest_tax_rate = cra["federal_brackets"][0][1]

    k1 = federal_lowest_tax_rate * federal_claim_amount

    k2 = federal_lowest_tax_rate * annual_base_cpp

    # T4127 factor K4:
    # Federal Canada Employment Amount tax credit
    canada_employment_amount = cra["canada_employment_amount"]

    k4 = min(
        federal_lowest_tax_rate * (pay_periods * payroll),
        federal_lowest_tax_rate * canada_employment_amount
    )

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

    lcf = 0.00

    # Calculate annual federal tax payable (T1).
    t1 = max(0, t3 - (pay_periods * lcf))

    federal_tax = t1 / pay_periods

    return federal_tax

def calculate_alberta_tax(
    annual_taxable_income,
    annual_base_cpp
):
    """Calculate Alberta income tax for one pay period."""
    pay_periods = cra["pay_periods"]

    # T4127: Select the Alberta tax bracket.
    alberta_rate, alberta_constant = get_tax_bracket(
        annual_taxable_income,
        cra["alberta_brackets"]
    )

    # T4127 factor K1P:
    # Alberta non-refundable personal tax credit.
    alberta_claim_amount = cra["alberta_claim_amount"]
    alberta_lowest_tax_rate = cra["alberta_brackets"][0][1]

    k1p = alberta_lowest_tax_rate * alberta_claim_amount

    # T4127 factor K2P:
    # Alberta tax credit for base CPP contributions.
    k2p = alberta_lowest_tax_rate * annual_base_cpp

    k3p = 0.00

    # Calculate basic Alberta tax (T4).
    t4 = (
        alberta_rate * annual_taxable_income
        - alberta_constant
        - k1p
        - k2p
        - k3p
    )
    
    # Annual Alberta tax payable (T2).
    t2 = t4

    # Convert annual Alberta tax to the current pay period.
    alberta_tax = t2 / pay_periods

    return alberta_tax


# Begin program

total = float(input("Enter total including GST: $"))

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

# Calculate annual values required by both federal and Alberta tax.
annual_taxable_income, annual_base_cpp = calculate_tax_inputs(
    payroll,
    employee_cpp,
    cra
)

# Calculate federal and Alberta income tax.
federal_tax = calculate_federal_tax(annual_taxable_income, annual_base_cpp, payroll)
alberta_tax = calculate_alberta_tax(annual_taxable_income, annual_base_cpp)

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
#print(f"Additional CPP (F5):     ${f5:,.2f}")
print(f"Annual taxable income A: ${annual_taxable_income:,.2f}")
#print(f"Federal rate (R):         {federal_rate:.1%}")
#print(f"Federal constant (K):     ${federal_constant:,.2f}")
#print(f"Federal claim amount (TC): ${federal_claim_amount:,.2f}")
#print(f"Federal tax credit (K1):   ${k1:,.2f}")
print(f"Annual base CPP:          ${annual_base_cpp:,.2f}")
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