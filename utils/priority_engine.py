def calculate_priority_score(hazard_counts, confidence_avg=0.5):
    """
    Computes a priority score (0-100), severity level, SLA target, 
    and recommended municipal department based on detected hazards.
    """
    # Infrastructure hazard risk weights mapping
    hazard_weights = {
        "damaged electrical infrastructure": 95,
        "live wire": 95,
        "transformer fault": 95,
        "deep pothole": 85,
        "pothole": 75,
        "road crack": 55,
        "garbage pile": 60,
        "overflowing dumpster": 55,
        "graffiti": 30,
        "illegal signboard": 40
    }
    
    base_score = 40  # Default baseline score
    
    if isinstance(hazard_counts, dict) and len(hazard_counts) > 0:
        max_weight = 40
        for hazard in hazard_counts.keys():
            h_lower = str(hazard).lower()
            matched_weight = 40
            for key, weight in hazard_weights.items():
                if key in h_lower:
                    matched_weight = weight
                    break
            if matched_weight > max_weight:
                max_weight = matched_weight
        base_score = max_weight
    
    # Scale score slightly based on YOLO confidence factor
    final_score = int(min(100, base_score * (0.85 + (0.3 * confidence_avg))))
    
    # Classify Severity, SLA, and Department
    if final_score >= 85:
        severity = "CRITICAL"
        sla_target = "2 Hours"
        assigned_dept = "Electrical & Emergency Response"
    elif final_score >= 65:
        severity = "HIGH"
        sla_target = "12 Hours"
        assigned_dept = "Road & Infrastructure Directorate"
    elif final_score >= 45:
        severity = "MEDIUM"
        sla_target = "24 Hours"
        assigned_dept = "Sanitation & Municipal Services"
    else:
        severity = "LOW"
        sla_target = "72 Hours"
        assigned_dept = "General Civic Maintenance"
        
    return {
        "priority_score": final_score,
        "severity": severity,
        "sla_target": sla_target,
        "assigned_dept": assigned_dept
    }
