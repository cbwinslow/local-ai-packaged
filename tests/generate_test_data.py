""
Test Data Generator for Government API Testing.

This script generates mock data for testing frontend and backend components
that interact with government APIs.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import faker
from faker.providers import company, date_time, lorem, person

# Initialize Faker
fake = faker.Faker()
fake.add_provider(company)
fake.add_provider(date_time)
fake.add_provider(lorem)
fake.add_provider(person)

class TestDataGenerator:
    """Generates test data for government API testing."""
    
    def __init__(self, output_dir: str = "test_data"):
        """Initialize with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Cache for generated data to maintain consistency
        self._cache: Dict[str, Any] = {}
    
    def generate_bill_data(self, count: int = 10) -> List[Dict]:
        """Generate mock bill data similar to Congress API."""
        bills = []
        bill_types = ['hr', 's', 'hres', 'sres', 'hjres', 'sjres', 'hconres', 'sconres']
        
        for i in range(count):
            bill_type = random.choice(bill_types)
            bill_number = random.randint(1, 5000)
            congress = random.randint(115, 118)  # Recent congresses
            
            bill = {
                'bill_id': f"{bill_type}{bill_number}-{congress}",
                'bill_type': bill_type,
                'number': str(bill_number),
                'congress': str(congress),
                'title': f"A bill to {fake.sentence().lower().capitalize()}",
                'short_title': f"{fake.catch_phrase()} Act of {2020 + random.randint(0, 5)}",
                'sponsor_title': random.choice(['Sen.', 'Rep.', '']),
                'sponsor_name': fake.name(),
                'sponsor_state': fake.state_abbr(),
                'sponsor_party': random.choice(['R', 'D', 'I']),
                'introduced_date': fake.date_between(start_date='-2y', end_date='today').isoformat(),
                'latest_major_action': random.choice([
                    'Referred to the Committee on Ways and Means.',
                    'Read twice and referred to the Committee on Finance.',
                    'Received in the Senate and Read twice and referred to the Committee on the Judiciary.',
                    'Became Public Law No: 117-103.'
                ]),
                'latest_major_action_date': fake.date_between(start_date='-1y', end_date='today').isoformat(),
                'govtrack_url': f"https://www.govtrack.us/congress/bills/{congress}/{bill_type}{bill_number}",
                'text_url': f"https://www.congress.gov/bill/{congress}th-congress/{bill_type}/{bill_number}/text",
                'subjects': random.sample([
                    'Taxation', 'Health', 'Armed forces and national security', 'Education',
                    'Environmental protection', 'Transportation and public works', 'Crime and law enforcement',
                    'International affairs', 'Energy', 'Labor and employment', 'Science, technology, communications'
                ], k=random.randint(1, 4)),
                'summary': fake.paragraph(nb_sentences=3),
                'actions': self._generate_bill_actions(),
                'committees': self._generate_committees(),
                'cosponsors': self._generate_cosponsors(random.randint(0, 20)),
                'status': random.choice(['introduced', 'referred', 'passed_house', 'passed_senate', 'enacted', 'vetoed'])
            }
            bills.append(bill)
        
        return bills
    
    def _generate_bill_actions(self) -> List[Dict]:
        """Generate a list of actions for a bill."""
        num_actions = random.randint(1, 8)
        actions = []
        date = fake.date_time_between(start_date='-2y', end_date='now')
        
        action_types = [
            ('Introduced', 'B00'),
            ('Referred to the Committee on Ways and Means.', '1000'),
            ('Committee Consideration and Mark-up Session Held by Committee on Finance.', '4000'),
            ('Committee on Finance. Ordered to be Reported (Amended) by the Yeas and Nays: 26 - 14.', '5000'),
            ('Reported (Amended) by the Committee on Finance. S. Rept. 117-123.', '8000'),
            ('Passed Senate with an amendment by Yea-Nay Vote. 69 - 30. Record Vote Number: 123.', '17000'),
            ('Message on Senate action sent to the House.', '28000'),
            ('Presented to President.', '37000'),
            ('Signed by President.', '36000'),
            ('Became Public Law No: 117-123.', '36000')
        ]
        
        # Always have at least one action
        action = random.choice(action_types)
        actions.append({
            'action_date': date.strftime('%Y-%m-%d'),
            'text': action[0],
            'action_code': action[1],
            'references': []
        })
        
        # Add more actions with increasing dates
        for _ in range(num_actions - 1):
            date += timedelta(days=random.randint(1, 30))
            action = random.choice(action_types)
            actions.append({
                'action_date': date.strftime('%Y-%m-%d'),
                'text': action[0],
                'action_code': action[1],
                'references': []
            })
        
        return sorted(actions, key=lambda x: x['action_date'])
    
    def _generate_committees(self) -> List[Dict]:
        """Generate committee data."""
        num_committees = random.randint(1, 3)
        committees = []
        
        common_committees = [
            'Committee on Finance',
            'Committee on Ways and Means',
            'Committee on the Judiciary',
            'Committee on Energy and Commerce',
            'Committee on Armed Services',
            'Committee on Health, Education, Labor, and Pensions',
            'Committee on Foreign Relations',
            'Committee on Appropriations'
        ]
        
        for _ in range(num_committees):
            committee = random.choice(common_committees)
            committees.append({
                'name': committee,
                'code': committee.upper().replace(' ', '_').replace(',', '').replace('-', '_'),
                'chamber': random.choice(['House', 'Senate', 'Joint']),
                'url': f"https://www.congress.gov/committee/{committee.lower().replace(' ', '-').replace(',', '')}"
            })
        
        return committees
    
    def _generate_cosponsors(self, count: int) -> List[Dict]:
        """Generate cosponsor data."""
        cosponsors = []
        
        for _ in range(count):
            cosponsors.append({
                'name': fake.name(),
                'state': fake.state_abbr(),
                'party': random.choice(['R', 'D', 'I']),
                'date': fake.date_between(start_date='-2y', end_date='today').isoformat(),
                'district': str(random.randint(1, 53)) if random.random() > 0.3 else None
            })
        
        return cosponsors
    
    def generate_regulation_data(self, count: int = 10) -> List[Dict]:
        """Generate mock regulation data similar to Regulations.gov API."""
        regulations = []
        
        for i in range(count):
            docket_id = f"{random.choice(['EPA', 'HHS', 'DOT', 'DOC', 'DOD'])}-{random.randint(2020, 2023)}-{random.randint(1000, 9999)}"
            comment_due_date = fake.date_between(start_date='today', end_date='+1y')
            
            regulation = {
                'id': f"REG-{random.randint(100000000, 999999999)}",
                'type': 'Rulemaking',
                'attributes': {
                    'title': f"{random.choice(['Revision', 'Amendment', 'New', 'Interim Final'])} of {fake.catch_phrase()}",
                    'docketId': docket_id,
                    'docketTitle': f"Regulation for {fake.catch_phrase()}",
                    'abstract': fake.paragraph(nb_sentences=3),
                    'documentType': random.choice(['Proposed Rule', 'Final Rule', 'Notice', 'Interim Final Rule']),
                    'frin': f"{random.randint(1000, 9999)}-{random.randint(10000, 99999)}",
                    'postedDate': fake.date_between(start_date='-1y', end_date='today').isoformat(),
                    'commentStartDate': fake.date_between(start_date='-30d', end_date='today').isoformat(),
                    'commentEndDate': comment_due_date.isoformat(),
                    'openForComment': comment_due_date > datetime.now().date(),
                    'agencyId': random.choice(['EPA', 'HHS', 'DOT', 'DOC', 'DOD']),
                    'agencyName': random.choice([
                        'Environmental Protection Agency',
                        'Department of Health and Human Services',
                        'Department of Transportation',
                        'Department of Commerce',
                        'Department of Defense'
                    ]),
                    'rin': f"{random.choice(['0584', '0910', '0938'])}-{random.choice(['AA', 'AB', 'AC'])}{random.randint(10, 99)}",
                    'cfrCitation': f"{random.randint(1, 50)} CFR {random.randint(100, 999)}.{random.randint(1, 99)}",
                    'documentNumber': f"{random.choice(['2022-', '2023-', '2024-'])}{random.randint(10000, 99999)}",
                    'pageCount': random.randint(5, 200),
                    'regulationType': random.choice(['Proposed Rule', 'Final Rule', 'Notice', 'Other']),
                    'regulationStatus': random.choice(['Open for Comment', 'Closed for Comment', 'Final']),
                    'regulationSubtype': random.choice(['Regular', 'Significant', 'Major', 'Other'])
                },
                'relationships': {
                    'agency': {
                        'data': {
                            'type': 'agency',
                            'id': f"{random.choice(['EPA', 'HHS', 'DOT', 'DOC', 'DOD'])}"
                        }
                    },
                    'docket': {
                        'data': {
                            'type': 'docket',
                            'id': docket_id
                        }
                    },
                    'documents': {
                        'data': [
                            {
                                'type': 'document',
                                'id': f"DOC-{random.randint(100000000, 999999999)}"
                            }
                        ]
                    }
                }
            }
            
            regulations.append(regulation)
        
        return regulations
    
    def generate_spending_data(self, count: int = 10) -> List[Dict]:
        """Generate mock spending data similar to USAspending API."""
        spending = []
        
        for i in range(count):
            award_id = random.randint(100000000, 999999999)
            amount = round(random.uniform(1000, 10000000), 2)
            
            spending.append({
                'id': award_id,
                'generated_internal_id': f"CONT_AWD_{award_id}_{fake.uuid4()}",
                'type': random.choice(['A', 'B', 'C', 'D']),  # A: Grant, B: Contract, etc.
                'type_description': random.choice([
                    'Defense Contract', 'Research Grant', 'Construction Contract',
                    'Service Contract', 'Cooperative Agreement'
                ]),
                'piid': f"{random.choice(['GS', 'FA', 'N', 'W'])}{random.choice(['A', 'B', 'C'])}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
                'awarding_agency': {
                    'id': random.randint(1, 1000),
                    'name': random.choice([
                        'Department of Defense',
                        'Department of Health and Human Services',
                        'Department of Education',
                        'Department of Transportation',
                        'National Science Foundation'
                    ]),
                    'toptier_agency': {
                        'code': random.choice(['012', '075', '089', '097', '123']),
                        'name': random.choice([
                            'Department of Defense',
                            'Department of Health and Human Services',
                            'Department of Education',
                            'Department of Transportation',
                            'National Science Foundation'
                        ])
                    }
                },
                'funding_agency': {
                    'id': random.randint(1, 1000),
                    'name': random.choice([
                        'Department of Defense',
                        'Department of Health and Human Services',
                        'Department of Education',
                        'Department of Transportation',
                        'National Science Foundation'
                    ]),
                    'toptier_agency': {
                        'code': random.choice(['012', '075', '089', '097', '123']),
                        'name': random.choice([
                            'Department of Defense',
                            'Department of Health and Human Services',
                            'Department of Education',
                            'Department of Transportation',
                            'National Science Foundation'
                        ])
                    }
                },
                'recipient': {
                    'recipient_name': fake.company(),
                    'recipient_unique_id': f"{random.randint(100000000, 999999999)}",
                    'recipient_uei': f"{random.choice(['ABC', 'DEF', 'GHI'])}{random.randint(1000000, 9999999)}",
                    'recipient_location': {
                        'location_country_code': 'USA',
                        'state_code': fake.state_abbr(),
                        'county_name': fake.county(),
                        'city_name': fake.city(),
                        'zip5': fake.zipcode()
                    }
                },
                'total_obligation': amount,
                'total_outlay': round(amount * random.uniform(0.1, 1.0), 2),
                'period_of_performance': {
                    'start_date': fake.date_between(start_date='-5y', end_date='today').isoformat(),
                    'end_date': fake.date_between(start_date='today', end_date='+5y').isoformat(),
                    'last_modified_date': fake.date_time_this_year().isoformat(),
                    'potential_end_date': fake.date_between(start_date='+1y', end_date='+10y').isoformat()
                },
                'description': f"Funding for {fake.catch_phrase()}",
                'place_of_performance': {
                    'country_code': 'USA',
                    'state_code': fake.state_abbr(),
                    'county_name': fake.county(),
                    'city_name': fake.city(),
                    'zip5': fake.zipcode()
                },
                'subaward_count': random.randint(0, 50),
                'total_subaward_amount': round(amount * random.uniform(0, 0.8), 2),
                'awarding_office': fake.company_suffix(),
                'funding_office': fake.company_suffix(),
                'date_signed': fake.date_this_decade().isoformat(),
                'last_modified_date': fake.date_time_this_year().isoformat(),
                'certified_date': fake.date_time_this_year().isoformat(),
                'create_date': fake.date_time_this_year().isoformat(),
                'update_date': fake.date_time_this_year().isoformat()
            })
        
        return spending
    
    def save_to_file(self, data: Any, filename: str, indent: int = 2):
        """Save data to a JSON file."""
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=indent)
        print(f"Saved {len(data) if isinstance(data, list) else 1} records to {filepath}")

def main():
    """Generate and save test data."""
    # Initialize the generator
    generator = TestDataGenerator(output_dir="test_data")
    
    # Generate and save test data
    print("Generating test data...")
    
    # Bills data (Congress API)
    bills = generator.generate_bill_data(count=20)
    generator.save_to_file(bills, 'bills.json')
    
    # Regulations data (Regulations.gov)
    regulations = generator.generate_regulation_data(count=15)
    generator.save_to_file(regulations, 'regulations.json')
    
    # Spending data (USAspending)
    spending = generator.generate_spending_data(count=25)
    generator.save_to_file(spending, 'spending.json')
    
    print("\nTest data generation complete!")
    print(f"Files saved to: {generator.output_dir.absolute()}")

if __name__ == "__main__":
    main()
