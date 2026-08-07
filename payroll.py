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

total = float(input("Enter total including GST: $"))

gst = total / 21
earned = total - gst

cpp_rate = 0.0595
monthly_cpp_exemption = 291.66

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

pay_periods = 12

# T4127 factor F5:
# Deductible additional CPP contribution
cpp_first_additional_rate = 0.0100

f5 = employee_cpp * (cpp_first_additional_rate / cpp_rate)

# T4127 Step 1:
# Annual taxable income (A)
annual_taxable_income = pay_periods * (payroll - f5)

if annual_taxable_income <= 55867:
    federal_rate = 0.15
    federal_constant = 0.00
elif annual_taxable_income <= 111733:
    federal_rate = 0.205
    federal_constant = 3072.69
elif annual_taxable_income <= 173205:
    federal_rate = 0.26
    federal_constant = 9217.99
elif annual_taxable_income <= 246752:
    federal_rate = 0.29
    federal_constant = 14414.14
else:
    federal_rate = 0.33
    federal_constant = 24284.22
    
# T4127 factor K1:
# Federal non-refundable personal tax credit
federal_claim_amount = 15705.00

k1 = 0.15 * federal_claim_amount

# T4127 factor K2:
# Federal tax credit for base CPP contributions
base_cpp_rate = 0.0495
max_annual_base_cpp = 3217.50

annual_base_cpp = min(
    base_cpp_rate * ((pay_periods * payroll) - 3500),
    max_annual_base_cpp
)

k2 = 0.15 * annual_base_cpp

# T4127 factor K4:
# Federal Canada Employment Amount tax credit
canada_employment_amount = 1433.00

k4 = min(
    0.15 * (pay_periods * payroll),
    0.15 * canada_employment_amount
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

# T4127 Step 4:
# Select Alberta tax rate (V) and constant (KP)
if annual_taxable_income <= 148269:
    alberta_rate = 0.10
    alberta_constant = 0.00
elif annual_taxable_income <= 177922:
    alberta_rate = 0.12
    alberta_constant = 2965.00
elif annual_taxable_income <= 237230:
    alberta_rate = 0.13
    alberta_constant = 4745.00
elif annual_taxable_income <= 355845:
    alberta_rate = 0.14
    alberta_constant = 7117.00
else:
    alberta_rate = 0.15
    alberta_constant = 10675.00
    
# Alberta factor K1P:
# Provincial non-refundable personal tax credit
alberta_claim_amount = 21885.00

k1p = 0.10 * alberta_claim_amount

# Alberta factor K2P:
# Provincial tax credit for base CPP contributions
alberta_lowest_tax_rate = 0.10

k2p = alberta_lowest_tax_rate * annual_base_cpp

# Other Alberta non-refundable tax credits
k3p = 0.00

# Annual basic Alberta tax
t4 = (
    alberta_rate * annual_taxable_income
    - alberta_constant
    - k1p
    - k2p
    - k3p
)

# T4127 Step 5:
# Annual Alberta tax payable
t2 = t4

# T4127 Step 6:
# Tax deductions for the monthly pay period
additional_tax = 0.00  # Factor L

federal_tax = t1 / pay_periods
alberta_tax = t2 / pay_periods

total_tax = federal_tax + alberta_tax + additional_tax

print(f"Total:  ${total:,.2f}")
print(f"GST:    ${gst:,.2f}")
print(f"Earned: ${earned:,.2f}")
#print(f"Estimated employer CPP: ${estimated_employer_cpp:,.2f}")
print(f"Payroll:                ${payroll:,.2f}")
print(f"Employee CPP:           ${employee_cpp:,.2f}")
print(f"Employer CPP:           ${employer_cpp:,.2f}")
print(f"Additional CPP (F5):     ${f5:,.2f}")
print(f"Annual taxable income A: ${annual_taxable_income:,.2f}")
print(f"Federal rate (R):         {federal_rate:.1%}")
print(f"Federal constant (K):     ${federal_constant:,.2f}")
print(f"Federal claim amount (TC): ${federal_claim_amount:,.2f}")
print(f"Federal tax credit (K1):   ${k1:,.2f}")
print(f"Annual base CPP:          ${annual_base_cpp:,.2f}")
print(f"Federal CPP credit (K2):  ${k2:,.2f}")
print(f"Canada Employment Amount: ${canada_employment_amount:,.2f}")
print(f"Federal employment credit (K4): ${k4:,.2f}")
print(f"Basic federal tax (T3):   ${t3:,.2f}")
print(f"Annual federal tax (T1):  ${t1:,.2f}")
print(f"Alberta rate (V):          {alberta_rate:.1%}")
print(f"Alberta constant (KP):     ${alberta_constant:,.2f}")
print(f"Alberta claim amount (TCP): ${alberta_claim_amount:,.2f}")
print(f"Alberta tax credit (K1P):   ${k1p:,.2f}")
print(f"Alberta CPP credit (K2P): ${k2p:,.2f}")
print(f"Basic Alberta tax (T4):   ${t4:,.2f}")
print(f"Annual Alberta tax (T2):  ${t2:,.2f}")
print(f"Federal tax for pay period: ${federal_tax:,.2f}")
print(f"Alberta tax for pay period: ${alberta_tax:,.2f}")
print(f"Total tax for pay period:   ${total_tax:,.2f}")