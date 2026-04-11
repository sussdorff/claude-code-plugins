#!/usr/bin/env python3
"""Generate sample LinkedIn GDPR export data for testing.

Creates a temporary directory with realistic but fake CSV files
matching the structure of a LinkedIn data export.

Usage:
    uv run python create_test_data.py [--output-dir /path/to/dir]
"""
from __future__ import annotations

import argparse
import csv
import random
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

FIRST_NAMES = [
    "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry",
    "Iris", "Jack", "Karen", "Leo", "Mia", "Noah", "Olivia", "Paul",
    "Quinn", "Rachel", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xander",
    "Yara", "Zach", "Anna", "Ben", "Clara", "David", "Elena", "Felix",
    "Greta", "Hans", "Ines", "Jan", "Katja", "Lars", "Marta", "Nils",
    "Otto", "Petra", "Rico", "Sven", "Tanja", "Udo", "Vera", "Wolfgang",
    "Xenia", "Yuki",
]

LAST_NAMES = [
    "Mueller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner",
    "Becker", "Schulz", "Hoffmann", "Koch", "Richter", "Wolf", "Klein",
    "Schroeder", "Neumann", "Braun", "Werner", "Schwarz", "Zimmermann",
    "Krueger", "Hartmann", "Lange", "Schmitt", "Krause", "Lehmann",
    "Anderson", "Thompson", "Garcia", "Martinez", "Robinson", "Clark",
    "Lewis", "Lee", "Walker", "Hall", "Allen", "Young", "King", "Wright",
    "Johnson", "Williams", "Brown", "Jones", "Davis", "Miller", "Wilson",
    "Moore", "Taylor", "Thomas",
]

COMPANIES = [
    "Google", "Microsoft", "Amazon", "Apple", "Meta", "SAP", "Siemens",
    "Deutsche Bank", "BMW Group", "Allianz", "Bosch", "Continental",
    "Zalando", "Delivery Hero", "N26", "Celonis", "Personio", "FlixBus",
    "Stripe", "Spotify", "Netflix", "Salesforce", "Adobe", "Databricks",
    "Snowflake", "Palantir", "Accenture", "McKinsey", "BCG", "Deloitte",
]

TITLES = [
    "Software Engineer", "Senior Software Engineer", "Staff Engineer",
    "Engineering Manager", "VP Engineering", "CTO", "CEO", "COO",
    "Product Manager", "Senior Product Manager", "Director of Product",
    "Data Scientist", "ML Engineer", "Data Engineer", "Analytics Lead",
    "UX Designer", "UI Designer", "Design Lead",
    "DevOps Engineer", "SRE", "Platform Engineer",
    "Sales Manager", "Account Executive", "Business Development Rep",
    "Marketing Manager", "Content Strategist", "Growth Lead",
    "HR Manager", "Recruiter", "Talent Acquisition Lead",
    "Consultant", "Senior Consultant", "Managing Director",
    "Founder", "Co-Founder", "Intern", "Working Student",
]

SKILLS = [
    "Python", "JavaScript", "TypeScript", "Java", "Go", "Rust", "C++",
    "React", "Angular", "Vue.js", "Node.js", "Django", "FastAPI",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
    "Data Analysis", "SQL", "PostgreSQL", "MongoDB", "Redis",
    "Agile", "Scrum", "Project Management", "Leadership",
    "Product Management", "UX Research", "Figma",
    "CI/CD", "Git", "Linux", "Microservices",
]

REACTION_TYPES = ["LIKE", "CELEBRATE", "SUPPORT", "LOVE", "INSIGHTFUL", "FUNNY"]

SAMPLE_POSTS = [
    "Excited to announce that I've just started a new role! Looking forward to the journey ahead.",
    "Great insights from today's conference on AI and the future of work. Key takeaway: adaptability is everything.",
    "Just published a new blog post about scaling distributed systems. Link in comments!",
    "Thrilled to share that our team just shipped a major product update. Months of hard work paying off.",
    "Reflecting on my career journey - 5 years ago I made a pivot that changed everything.",
    "Hot take: the best code is the code you don't write. Simplicity always wins.",
    "Had an amazing conversation about leadership today. The best leaders create more leaders.",
    "Our team is hiring! If you're passionate about building great products, let's talk.",
    "Just completed a certification in cloud architecture. Never stop learning!",
    "The tech industry needs more diversity. Here's what we're doing about it at our company.",
    "Lessons learned from our latest production incident. Thread below.",
    "Grateful for the amazing team I get to work with every day.",
]

SAMPLE_COMMENTS = [
    "Great post! Totally agree with this perspective.",
    "Thanks for sharing these insights.",
    "This is exactly what the industry needs right now.",
    "Congrats on the new role!",
    "Would love to connect and discuss this further.",
    "Spot on analysis. We've seen similar patterns.",
    "Interesting take - have you considered the impact on smaller teams?",
    "Well said! Sharing with my team.",
]


def random_date(start_year: int = 2018, end_year: int = 2025) -> datetime:
    """Generate a random datetime within the given year range."""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    """Write rows to a CSV file with BOM for realism."""
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def create_connections(output_dir: Path, count: int = 60) -> None:
    """Generate Connections.csv with sample data."""
    fieldnames = ["First Name", "Last Name", "Email Address", "Company", "Position", "Connected On"]
    rows = []
    for _ in range(count):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        email = f"{first.lower()}.{last.lower()}@example.com"
        company = random.choice(COMPANIES) if random.random() > 0.1 else ""
        position = random.choice(TITLES) if random.random() > 0.05 else ""
        date = random_date(2018, 2025)
        rows.append({
            "First Name": first,
            "Last Name": last,
            "Email Address": email if random.random() > 0.3 else "",
            "Company": company,
            "Position": position,
            "Connected On": date.strftime("%d %b %Y"),
        })
    write_csv(output_dir / "Connections.csv", fieldnames, rows)


def create_messages(output_dir: Path, count: int = 30) -> None:
    """Generate Messages.csv with sample data."""
    fieldnames = ["CONVERSATION ID", "CONVERSATION TITLE", "FROM", "SENDER PROFILE URL", "TO", "DATE", "SUBJECT", "CONTENT"]
    rows = []
    conv_count = max(count // 4, 5)
    conversations = [f"conv-{i:04d}" for i in range(conv_count)]
    for _ in range(count):
        conv_id = random.choice(conversations)
        from_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        to_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        date = random_date(2020, 2025)
        rows.append({
            "CONVERSATION ID": conv_id,
            "CONVERSATION TITLE": f"Chat with {from_name}",
            "FROM": from_name,
            "SENDER PROFILE URL": f"https://www.linkedin.com/in/{from_name.lower().replace(' ', '-')}",
            "TO": to_name,
            "DATE": date.strftime("%Y-%m-%d %H:%M:%S"),
            "SUBJECT": "",
            "CONTENT": f"Hi {to_name.split()[0]}, thanks for connecting!",
        })
    write_csv(output_dir / "Messages.csv", fieldnames, rows)


def create_positions(output_dir: Path) -> None:
    """Generate Positions.csv with sample career history."""
    fieldnames = ["Company Name", "Title", "Description", "Location", "Started On", "Finished On"]
    positions = [
        {"Company Name": "TechCorp GmbH", "Title": "Junior Developer", "Description": "Building web apps", "Location": "Berlin, Germany", "Started On": "Jan 2018", "Finished On": "Dec 2019"},
        {"Company Name": "ScaleUp AG", "Title": "Senior Engineer", "Description": "Leading backend team", "Location": "Munich, Germany", "Started On": "Jan 2020", "Finished On": "Jun 2022"},
        {"Company Name": "BigTech Inc", "Title": "Staff Engineer", "Description": "Platform architecture", "Location": "Berlin, Germany", "Started On": "Jul 2022", "Finished On": ""},
    ]
    write_csv(output_dir / "Positions.csv", fieldnames, positions)


def create_profile(output_dir: Path) -> None:
    """Generate Profile.csv with sample profile data."""
    fieldnames = ["First Name", "Last Name", "Maiden Name", "Address", "Birth Date", "Headline", "Summary", "Industry", "Geo Location"]
    rows = [{
        "First Name": "Max",
        "Last Name": "Mustermann",
        "Maiden Name": "",
        "Address": "Berlin, Germany",
        "Birth Date": "",
        "Headline": "Staff Engineer | Building scalable systems",
        "Summary": "Passionate about distributed systems, cloud architecture, and mentoring engineers.",
        "Industry": "Information Technology & Services",
        "Geo Location": "Berlin, Berlin, Germany",
    }]
    write_csv(output_dir / "Profile.csv", fieldnames, rows)


def create_skills(output_dir: Path) -> None:
    """Generate Skills.csv with sample skills."""
    fieldnames = ["Name"]
    selected = random.sample(SKILLS, min(25, len(SKILLS)))
    rows = [{"Name": skill} for skill in selected]
    write_csv(output_dir / "Skills.csv", fieldnames, rows)


def create_endorsements(output_dir: Path) -> None:
    """Generate Endorsement Received Info.csv."""
    fieldnames = ["Skill Name", "Endorser First Name", "Endorser Last Name", "Endorsement Date"]
    rows = []
    endorsed_skills = random.sample(SKILLS, min(12, len(SKILLS)))
    for skill in endorsed_skills:
        endorsement_count = random.randint(1, 8)
        for _ in range(endorsement_count):
            date = random_date(2019, 2025)
            rows.append({
                "Skill Name": skill,
                "Endorser First Name": random.choice(FIRST_NAMES),
                "Endorser Last Name": random.choice(LAST_NAMES),
                "Endorsement Date": date.strftime("%d %b %Y"),
            })
    write_csv(output_dir / "Endorsement Received Info.csv", fieldnames, rows)


def create_shares(output_dir: Path, count: int = 12) -> None:
    """Generate Shares.csv with sample posts."""
    fieldnames = ["Date", "ShareLink", "ShareCommentary", "SharedUrl", "MediaUrl"]
    rows = []
    for i in range(count):
        date = random_date(2020, 2025)
        text = SAMPLE_POSTS[i % len(SAMPLE_POSTS)]
        rows.append({
            "Date": date.strftime("%Y-%m-%d %H:%M:%S"),
            "ShareLink": f"https://www.linkedin.com/feed/update/urn:li:activity:{random.randint(10**18, 10**19)}",
            "ShareCommentary": text,
            "SharedUrl": f"https://example.com/article-{i}" if random.random() > 0.5 else "",
            "MediaUrl": f"https://example.com/image-{i}.jpg" if random.random() > 0.7 else "",
        })
    write_csv(output_dir / "Shares.csv", fieldnames, rows)


def create_reactions(output_dir: Path, count: int = 40) -> None:
    """Generate Reactions.csv with sample engagement data."""
    fieldnames = ["Date", "Type", "Link"]
    rows = []
    for _ in range(count):
        date = random_date(2020, 2025)
        rows.append({
            "Date": date.strftime("%Y-%m-%d %H:%M:%S"),
            "Type": random.choice(REACTION_TYPES),
            "Link": f"https://www.linkedin.com/feed/update/urn:li:activity:{random.randint(10**18, 10**19)}",
        })
    write_csv(output_dir / "Reactions.csv", fieldnames, rows)


def create_invitations(output_dir: Path, count: int = 25) -> None:
    """Generate Invitations.csv with sample invitation data."""
    fieldnames = ["From", "To", "Date", "Message", "Direction"]
    rows = []
    for _ in range(count):
        from_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        to_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        date = random_date(2019, 2025)
        direction = random.choice(["OUTGOING", "INCOMING"])
        message = "I'd like to add you to my professional network." if random.random() > 0.4 else ""
        rows.append({
            "From": from_name,
            "To": to_name,
            "Date": date.strftime("%d %b %Y"),
            "Message": message,
            "Direction": direction,
        })
    write_csv(output_dir / "Invitations.csv", fieldnames, rows)


def create_comments(output_dir: Path, count: int = 15) -> None:
    """Generate Comments.csv with sample comments."""
    fieldnames = ["Date", "Link", "Message"]
    rows = []
    for i in range(count):
        date = random_date(2020, 2025)
        rows.append({
            "Date": date.strftime("%Y-%m-%d %H:%M:%S"),
            "Link": f"https://www.linkedin.com/feed/update/urn:li:activity:{random.randint(10**18, 10**19)}",
            "Message": SAMPLE_COMMENTS[i % len(SAMPLE_COMMENTS)],
        })
    write_csv(output_dir / "Comments.csv", fieldnames, rows)


def create_test_export(output_dir: Path | None = None) -> Path:
    """Create a complete test GDPR export directory."""
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="linkedin_gdpr_test_"))
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    random.seed(42)  # Reproducible test data

    create_connections(output_dir, count=60)
    create_messages(output_dir, count=30)
    create_positions(output_dir)
    create_profile(output_dir)
    create_skills(output_dir)
    create_endorsements(output_dir)
    create_shares(output_dir, count=12)
    create_reactions(output_dir, count=40)
    create_invitations(output_dir, count=25)
    create_comments(output_dir, count=15)

    return output_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate sample LinkedIn GDPR export data for testing."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to create test data in (default: temp directory)",
    )
    args = parser.parse_args()

    output_dir = create_test_export(args.output_dir)

    print(f"Test GDPR export created at: {output_dir}")
    print()
    print("Files created:")
    for csv_file in sorted(output_dir.glob("*.csv")):
        # Count rows (subtract header)
        with csv_file.open(encoding="utf-8-sig") as f:
            line_count = sum(1 for _ in f) - 1
        print(f"  {csv_file.name}: {line_count} rows")


if __name__ == "__main__":
    main()
