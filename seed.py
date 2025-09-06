import db

# Example subjects for B.Tech ECE
subjects = [
    ("ECT203", "Signals and Systems"),
    ("EC400", "Digital Signal Processing"),
    ("EC401", "Communication Engineering"),
]

for code, name in subjects:
    db.add_subject(code, name)

print("✅ Subjects seeded.")
