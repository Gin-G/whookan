#!/usr/bin/env python3
"""
Script to generate thousands of dummy user accounts for testing
Creates realistic companies with employees having relevant skills
"""

import re
import asyncio
import aiohttp
import random
from typing import List, Dict, Set
from faker import Faker
import json

fake = Faker()

# Configuration
API_BASE_URL = "https://whokan.nickknows.net/api/v1"
TOTAL_USERS = 3000
COMPANIES_COUNT = 50
CONCURRENT_REQUESTS = 2  # Reduced for better stability
CHUNK_SIZE = 10

# Company types and their common skills
COMPANY_PROFILES = {
    "tech_startup": {
        "suffixes": ["Labs", "Tech", "AI", "Solutions", "Systems", "Digital"],
        "titles": [
            "Software Engineer", "DevOps Engineer", "Data Scientist", "Product Manager",
            "Backend Developer", "Frontend Developer", "Full Stack Developer", 
            "Site Reliability Engineer", "Cloud Architect", "ML Engineer"
        ],
        "skills": [
            "Python", "JavaScript", "React", "Node.js", "AWS", "Docker", "Kubernetes",
            "PostgreSQL", "MongoDB", "Redis", "Git", "CI/CD", "Terraform", "Machine Learning"
        ]
    },
    "consulting": {
        "suffixes": ["Consulting", "Advisory", "Partners", "Group", "Associates"],
        "titles": [
            "Senior Consultant", "Principal Consultant", "Business Analyst", 
            "Project Manager", "Strategy Consultant", "Technical Consultant",
            "Implementation Specialist", "Solutions Architect"
        ],
        "skills": [
            "Project Management", "Business Analysis", "SQL", "Excel", "PowerBI", 
            "Tableau", "Salesforce", "SAP", "Agile", "Scrum", "Strategy", "Process Improvement"
        ]
    },
    "finance": {
        "suffixes": ["Capital", "Investments", "Financial", "Bank", "Holdings", "Asset Management"],
        "titles": [
            "Financial Analyst", "Investment Analyst", "Portfolio Manager", "Risk Analyst",
            "Quantitative Analyst", "Compliance Officer", "Trader", "Research Analyst"
        ],
        "skills": [
            "Excel", "SQL", "Python", "R", "Financial Modeling", "Risk Management",
            "Bloomberg", "VBA", "Tableau", "Statistics", "Derivatives", "Fixed Income"
        ]
    },
    "healthcare": {
        "suffixes": ["Health", "Medical", "Healthcare", "Clinic", "Hospital System"],
        "titles": [
            "Data Analyst", "Health Informatics Specialist", "Clinical Researcher",
            "Healthcare Consultant", "Biostatistician", "Medical Software Developer",
            "Health Data Manager", "Clinical Systems Analyst"
        ],
        "skills": [
            "SQL", "R", "Python", "SAS", "SPSS", "Clinical Research", "HIPAA",
            "Electronic Health Records", "Healthcare Analytics", "Biostatistics"
        ]
    },
    "ecommerce": {
        "suffixes": ["Commerce", "Retail", "Marketplace", "Shopping", "Store"],
        "titles": [
            "E-commerce Manager", "Digital Marketing Manager", "Product Manager",
            "Data Analyst", "UX Designer", "Growth Manager", "Operations Manager"
        ],
        "skills": [
            "Google Analytics", "SQL", "Python", "A/B Testing", "SEO", "SEM",
            "Shopify", "Magento", "Customer Analytics", "Conversion Optimization"
        ]
    }
}

# Additional skills that can appear across industries
GENERAL_SKILLS = [
    "Leadership", "Communication", "Teamwork", "Problem Solving", "Critical Thinking",
    "Time Management", "Negotiation", "Presentation", "Customer Service", "Training",
    "Documentation", "Quality Assurance", "Testing", "Debugging", "Code Review"
]

# HR and general corporate skills
HR_CORPORATE_SKILLS = [
    "HR", "Recruiting", "Talent Acquisition", "Performance Management", "HRIS",
    "Payroll", "Benefits Administration", "Employee Relations", "Training & Development",
    "Compliance", "Legal", "Contract Management", "Vendor Management", "Budgeting",
    "Accounting", "Finance", "Marketing", "Sales", "Customer Success"
]

def sanitize_domain_name(company_name: str) -> str:
    """
    Convert company name to a valid domain name format
    """
    # Convert to lowercase
    domain = company_name.lower()
    
    # Replace spaces, commas, and other special characters with hyphens
    domain = re.sub(r'[^a-z0-9]', '-', domain)
    
    # Remove multiple consecutive hyphens
    domain = re.sub(r'-+', '-', domain)
    
    # Remove leading/trailing hyphens
    domain = domain.strip('-')
    
    # Ensure domain isn't empty
    if not domain:
        domain = "company"
    
    return domain

def is_valid_email(email: str) -> bool:
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_companies() -> List[Dict]:
    """Generate realistic company profiles"""
    companies = []
    
    for _ in range(COMPANIES_COUNT):
        company_type = random.choice(list(COMPANY_PROFILES.keys()))
        profile = COMPANY_PROFILES[company_type]
        
        # Generate company name
        base_name = fake.company().split()[0]  # Take first word of fake company
        suffix = random.choice(profile["suffixes"])
        company_name = f"{base_name} {suffix}"
        
        # Determine company size (affects skill distribution)
        size = random.choices(
            ["small", "medium", "large"], 
            weights=[0.4, 0.4, 0.2]
        )[0]
        
        employee_count = {
            "small": random.randint(10, 50),
            "medium": random.randint(51, 200), 
            "large": random.randint(201, 500)
        }[size]
        
        companies.append({
            "name": company_name,
            "type": company_type,
            "size": size,
            "employee_count": employee_count,
            "profile": profile
        })
    
    return companies

def generate_user_for_company(company: Dict) -> Dict:
    """Generate a user profile for a specific company with fixed email generation"""
    profile = company["profile"]
    
    # Basic user info
    first_name = fake.first_name()
    last_name = fake.last_name()
    
    # Fixed email generation with proper domain sanitization
    domain = sanitize_domain_name(company['name'])
    email = f"{first_name.lower()}.{last_name.lower()}@{domain}.com"
    
    # Validate the generated email (optional safety check)
    if not is_valid_email(email):
        print(f"Warning: Generated potentially invalid email: {email}")
        # Fallback to a generic domain if validation fails
        email = f"{first_name.lower()}.{last_name.lower()}@company.com"
    
    # Select title based on company type
    title = random.choice(profile["titles"])
    
    # Add some HR/corporate roles for larger companies
    if company["size"] in ["medium", "large"] and random.random() < 0.15:
        hr_titles = [
            "HR Manager", "Talent Acquisition Specialist", "Operations Manager",
            "Finance Manager", "Marketing Manager", "Sales Manager", "Legal Counsel"
        ]
        title = random.choice(hr_titles)
    
    # Generate skills based on company type and role
    skills = set()
    
    # Core company skills (higher probability)
    company_skills = random.sample(
        profile["skills"], 
        random.randint(3, min(8, len(profile["skills"])))
    )
    skills.update(company_skills)
    
    # Add some general skills
    general_skills = random.sample(
        GENERAL_SKILLS,
        random.randint(2, 5)
    )
    skills.update(general_skills)
    
    # Add HR/corporate skills for certain roles or randomly
    if "HR" in title or "Manager" in title or random.random() < 0.2:
        hr_skills = random.sample(
            HR_CORPORATE_SKILLS,
            random.randint(1, 4)
        )
        skills.update(hr_skills)
    
    # Convert skills to list
    skills_list = list(skills)
    
    return {
        "user_data": {
            "email": email,
            "name": f"{first_name} {last_name}",
            "password": "temppass123",
            "title": title,
            "company": company["name"]
        },
        "skills": skills_list  # Keep skills separate for the skills API call
    }

async def authenticate_user(session: aiohttp.ClientSession, email: str, password: str) -> str:
    """Authenticate a user and return the access token"""
    try:
        async with session.post(
            f"{API_BASE_URL}/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("access_token")
            else:
                error_text = await response.text()
                print(f"Failed to authenticate {email}: {response.status} - {error_text}")
                return None
    except Exception as e:
        print(f"Error authenticating {email}: {str(e)}")
        return None

async def add_skills_to_user(session: aiohttp.ClientSession, token: str, skills: List[str]) -> bool:
    """Add skills to a user using the bulk skills API"""
    try:
        # Format skills as newline-separated string (as per API docs default)
        skills_formatted = "\n".join(skills)
        
        async with session.post(
            f"{API_BASE_URL}/users/me/skills/bulk",
            json={
                "skills": skills_formatted,
                "format": "newline"  # Using the default format from API docs
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        ) as response:
            if response.status == 200:
                return True
            else:
                error_text = await response.text()
                print(f"Failed to add skills: {response.status} - {error_text}")
                return False
    except Exception as e:
        print(f"Error adding skills: {str(e)}")
        return False

async def create_user_with_skills(session: aiohttp.ClientSession, user_profile: Dict, semaphore: asyncio.Semaphore) -> bool:
    """Create a user and add their skills with improved error handling"""
    async with semaphore:
        try:
            # Step 1: Create the user
            async with session.post(
                f"{API_BASE_URL}/users/",
                json=user_profile["user_data"],
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"Failed to create user {user_profile['user_data']['email']}: {response.status} - {error_text}")
                    return False
                
                # Get the created user data
                user_data = await response.json()
                print(f"Successfully created user: {user_profile['user_data']['email']}")
            
            # Step 2: Wait longer for user creation to be fully committed
            await asyncio.sleep(2.0)  # Increased from 0.5 to 2.0 seconds
            
            # Step 3: Authenticate as the new user (with retries and exponential backoff)
            token = None
            for attempt in range(5):  # Increased from 3 to 5 attempts
                token = await authenticate_user(
                    session, 
                    user_profile["user_data"]["email"], 
                    user_profile["user_data"]["password"]
                )
                if token:
                    break
                wait_time = (2 ** attempt)  # Exponential backoff: 1, 2, 4, 8, 16 seconds
                print(f"Authentication attempt {attempt + 1} failed for {user_profile['user_data']['email']}, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            
            if not token:
                print(f"Failed to authenticate user {user_profile['user_data']['email']} after 5 attempts")
                return False
            
            # Step 4: Add skills to the user (with retries and exponential backoff)
            if user_profile["skills"]:
                skills_added = False
                for attempt in range(5):  # Increased from 3 to 5 attempts
                    skills_added = await add_skills_to_user(session, token, user_profile["skills"])
                    if skills_added:
                        break
                    wait_time = (2 ** attempt)  # Exponential backoff
                    print(f"Skills addition attempt {attempt + 1} failed for {user_profile['user_data']['email']}, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                
                if not skills_added:
                    print(f"User created but failed to add skills for {user_profile['user_data']['email']} after 5 attempts")
                    return False
            
            print(f"Successfully created user with skills: {user_profile['user_data']['email']}")
            return True
            
        except Exception as e:
            print(f"Error creating user with skills {user_profile['user_data']['email']}: {str(e)}")
            return False

async def create_users_batch(user_profiles: List[Dict]) -> Dict[str, int]:
    """Create users with skills in batches with improved concurrency control"""
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
    stats = {"success": 0, "failed": 0}
    
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=120)  # Increased timeout to 2 minutes
    ) as session:
        tasks = []
        for user_profile in user_profiles:
            task = create_user_with_skills(session, user_profile, semaphore)
            tasks.append(task)
        
        # Process in smaller chunks with longer delays
        chunk_size = CHUNK_SIZE  # Use the reduced chunk size
        for i in range(0, len(tasks), chunk_size):
            chunk = tasks[i:i + chunk_size]
            results = await asyncio.gather(*chunk, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    print(f"Exception occurred: {result}")
                    stats["failed"] += 1
                elif result:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
            
            print(f"Processed {min(i + chunk_size, len(tasks))}/{len(tasks)} users...")
            print(f"Current stats - Success: {stats['success']}, Failed: {stats['failed']}")
            
            # Much longer delay between chunks to reduce database load
            if i + chunk_size < len(tasks):  # Don't sleep after the last chunk
                await asyncio.sleep(5.0)  # Increased from 2.0 to 5.0 seconds
    
    return stats

def main():
    """Main function to generate and create users"""
    print(f"Generating {TOTAL_USERS} users across {COMPANIES_COUNT} companies...")
    
    # Generate companies
    companies = generate_companies()
    print(f"Generated {len(companies)} companies")
    
    # Calculate users per company (roughly)
    total_employees = sum(company["employee_count"] for company in companies)
    scale_factor = TOTAL_USERS / total_employees
    
    # Generate user profiles (with skills)
    all_user_profiles = []
    for company in companies:
        target_employees = max(1, int(company["employee_count"] * scale_factor))
        
        print(f"Generating {target_employees} users for {company['name']}")
        
        for _ in range(target_employees):
            user_profile = generate_user_for_company(company)
            all_user_profiles.append(user_profile)
    
    print(f"Generated {len(all_user_profiles)} total user profiles")
    
    # Save user profiles to file for backup/review
    with open("generated_user_profiles.json", "w") as f:
        json.dump(all_user_profiles, f, indent=2)
    print("Saved user profile data to generated_user_profiles.json")
    
    # Create users with skills via API
    print("Starting user creation with skills via API...")
    stats = asyncio.run(create_users_batch(all_user_profiles))
    
    print(f"\nUser creation completed!")
    print(f"Successfully created: {stats['success']} users with skills")
    print(f"Failed to create: {stats['failed']} users")
    
    # Print some sample companies and their skills
    print("\nSample companies and common skills:")
    for company in companies[:5]:
        sample_skills = set()
        company_users = [u for u in all_user_profiles if u["user_data"]["company"] == company["name"]]
        for user in company_users[:3]:  # Sample first 3 users
            sample_skills.update(user["skills"][:5])  # First 5 skills
        print(f"\n{company['name']} ({company['type']}, {len(company_users)} employees)")
        print(f"Sample skills: {', '.join(list(sample_skills)[:10])}")

if __name__ == "__main__":
    # Install required packages if not already installed
    try:
        import aiohttp
        from faker import Faker
    except ImportError:
        print("Please install required packages:")
        print("pip install aiohttp faker")
        exit(1)
    
    main()