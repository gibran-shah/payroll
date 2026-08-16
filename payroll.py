CRA = {
    2024: {
        # Pay periods
        "pay_periods": 12,

        # CPP
        "cpp_rate": 0.0595,
        "cpp_basic_exemption": 3500.00,
        "monthly_cpp_exemption": 291.66,
        "cpp_first_additional_rate": 0.0100,
        "max_annual_base_cpp": 3217.50,
        "base_cpp_rate": 0.0495,

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

cra = CRA[2024]



def calculate_cpp(amount, cpp_rate, monthly_cpp_exemption):
    return max(
        0,
        (amount - monthly_cpp_exemption) * cpp_rate
    )


def calculate_payroll(
    payroll_before_employer_cpp,
    cpp_rate,
    monthly_cpp_exemption
):
    estimated_employer_cpp = calculate_cpp(
        payroll_before_employer_cpp,
        cpp_rate,
        monthly_cpp_exemption
    )

    return payroll_before_employer_cpp - estimated_employer_cpp
    
def get_tax_bracket(annual_taxable_income, brackets):
    for upper_limit, rate, constant in brackets:
        if annual_taxable_income <= upper_limit:
            return rate, constant

    raise ValueError("No tax bracket found")
    
def calculate_tax_inputs(payroll, employee_cpp, cra):
    pay_periods = cra["pay_periods"]

    # T4127 factor F5:
    # Deductible additional CPP contribution
    cpp_first_additional_rate = cra["cpp_first_additional_rate"]

    f5 = employee_cpp * (
        cpp_first_additional_rate / cra["cpp_rate"]
    )

    # T4127 Step 1:
    # Annual taxable income (A)
    annual_taxable_income = pay_periods * (payroll - f5)

    # T4127 factor K2:
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
    
def calculate_federal_tax(payroll, employee_cpp, cra):
    pay_periods = cra["pay_periods"]

    # T4127 factor F5:
    # Deductible additional CPP contribution
    cpp_first_additional_rate = cra["cpp_first_additional_rate"]

    federal_rate, federal_constant = get_tax_bracket(
        annual_taxable_income,
        cra["federal_brackets"]
    )

    # T4127 factor K1:
    # Federal non-refundable personal tax credit
    federal_claim_amount = cra["federal_claim_amount"]
    federal_lowest_tax_rate = cra["federal_brackets"][0][1]

    k1 = federal_lowest_tax_rate * federal_claim_amount

    # T4127 factor K2:
    # Federal tax credit for base CPP contributions
    base_cpp_rate = 0.0495
    max_annual_base_cpp = cra["max_annual_base_cpp"]

    annual_base_cpp = min(
        base_cpp_rate * ((pay_periods * payroll) - 3500),
        max_annual_base_cpp
    )

    k2 = federal_lowest_tax_rate * annual_base_cpp

    # T4127 factor K4:
    # Federal Canada Employment Amount tax credit
    canada_employment_amount = cra["canada_employment_amount"]

    k4 = min(
        federal_lowest_tax_rate * (pay_periods * payroll),
        federal_lowest_tax_rate * canada_employment_amount
    )

    # T4127 Step 2:
    # Basic federal tax
    k3 = 0.00

    t3 = (
        federal_rate * annual_taxable_income
        - federal_constant
        - k1
        - k2
        - k3
        - k4
    )

    # T4127 Step 3:
    # Annual federal tax payable
    lcf = 0.00

    t1 = max(0, t3 - (pay_periods * lcf))

    federal_tax = t1 / pay_periods

    return federal_tax

def calculate_alberta_tax(
    annual_taxable_income,
    annual_base_cpp,
    cra
):
    pay_periods = cra["pay_periods"]

    # Alberta tax bracket
    alberta_rate, alberta_constant = get_tax_bracket(
        annual_taxable_income,
        cra["alberta_brackets"]
    )

    # T4127 factor K1P:
    # Alberta non-refundable personal tax credit
    alberta_claim_amount = cra["alberta_claim_amount"]
    alberta_lowest_tax_rate = cra["alberta_brackets"][0][1]

    k1p = alberta_lowest_tax_rate * alberta_claim_amount

    # T4127 factor K2P:
    # Alberta tax credit for base CPP contributions
    k2p = alberta_lowest_tax_rate * annual_base_cpp

    # T4127 Step 4:
    # Basic Alberta tax
    k3p = 0.00

    t4 = (
        alberta_rate * annual_taxable_income
        - alberta_constant
        - k1p
        - k2p
        - k3p
    )

    # T4127 Step 5:
    # Annual Alberta tax payable
    #lcp = 0.00

    #t2 = max(0, t4 - (pay_periods * lcp))
    
    t2 = t4

    # T4127 Step 6:
    # Alberta tax for the pay period
    alberta_tax = t2 / pay_periods

    return alberta_tax

total = float(input("Enter total including GST: $"))

gst = total / 21
earned = total - gst

cpp_rate = cra["cpp_rate"]
monthly_cpp_exemption = cra["monthly_cpp_exemption"]

payroll = calculate_payroll(
    earned,
    cpp_rate,
    monthly_cpp_exemption
)

employee_cpp = calculate_cpp(
    payroll,
    cpp_rate,
    monthly_cpp_exemption
)

employer_cpp = employee_cpp

annual_taxable_income, annual_base_cpp = calculate_tax_inputs(
    payroll,
    employee_cpp,
    cra
)

federal_tax = calculate_federal_tax(
    payroll,
    employee_cpp,
    cra
)

alberta_tax = calculate_alberta_tax(
    annual_taxable_income,
    annual_base_cpp,
    cra
)

total_tax = federal_tax + alberta_tax

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