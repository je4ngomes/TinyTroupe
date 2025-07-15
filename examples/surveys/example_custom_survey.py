#!/usr/bin/env python3
"""
Custom Survey Example
Demonstrates how to create targeted surveys for specific demographics and ad types.
"""

from minimal_avatar_survey import AvatarFactory, AdEvaluator, SurveyRunner

def main():
    print("🎯 Custom Marketing Survey Example")
    print("=" * 50)
    
    # Create evaluator and survey runner
    evaluator = AdEvaluator()
    survey = SurveyRunner(evaluator)
    
    # Example 1: Gaming Laptop Survey for Tech-Savvy Millennials
    print("\n📱 Survey 1: Gaming Laptops for Tech-Savvy Millennials")
    print("-" * 55)
    
    # Generate targeted avatars
    gaming_avatars = AvatarFactory.generate_targeted_avatars(
        target_demographics={
            "age_range": (25, 40),
            "income_levels": ["medium", "high"], 
            "required_interests": ["Gaming", "Technology"]
        },
        count=8
    )
    
    # Define gaming laptop ads
    gaming_ads = [
        {
            "id": "Gaming_Pro",
            "title": "High-Performance Gaming Laptop",
            "content": """
🎮 ULTIMATE GAMING BEAST 🎮

ROG Strix X17 - Dominate Every Game
• Intel i9-13980HX Processor
• RTX 4080 Graphics Card  
• 32GB DDR5 RAM
• 1TB NVMe SSD
• 17.3" 360Hz Display

Was $2,799 → NOW $2,299
FREE RGB Gaming Mouse + Headset!

"Best gaming laptop I've ever owned!" ⭐⭐⭐⭐⭐
Order now - Limited stock!
"""
        },
        {
            "id": "Gaming_Budget",
            "title": "Affordable Gaming Laptop", 
            "content": """
Gaming Laptop - Great Performance, Great Price

MSI GF63 Thin - Game On A Budget
- Intel i5-12450H processor
- GTX 1650 graphics
- 16GB RAM, 512GB SSD
- 15.6" FHD display
- Lightweight design

Only $699 (Reg. $899)
Perfect for casual and competitive gaming
Free shipping + 2 year warranty included
"""
        },
        {
            "id": "Gaming_Content",
            "title": "Creator Gaming Laptop",
            "content": """
ALIENWARE x15 R2 - Game & Create

Perfect for Gaming + Content Creation
✓ Intel i7-12700H + RTX 4070
✓ 32GB RAM + 1TB SSD
✓ 15.6" QHD 240Hz G-SYNC
✓ Advanced cooling system
✓ Customizable RGB lighting

Professional Performance: $2,199
0% APR financing for 24 months
Used by top streamers and esports pros
"""
        }
    ]
    
    # Run gaming survey
    gaming_results = survey.run_ad_comparison(
        ads=gaming_ads,
        avatars=gaming_avatars,
        context="You're looking to upgrade your gaming setup for better performance in the latest games."
    )
    
    print(f"Gaming Survey Results:")
    for ad_id, stats in gaming_results["summary"].items():
        if ad_id != "winner":
            print(f"  {ad_id}: {stats['average_rating']:.1f}/10 avg ({stats['high_engagement']} highly engaged)")
    print(f"🏆 Winner: {gaming_results['summary']['winner']['ad_id']}")
    
    # Example 2: Health Supplements for Health-Conscious Adults
    print("\n🥗 Survey 2: Health Supplements for Health-Conscious Adults")
    print("-" * 62)
    
    # Generate health-focused avatars
    health_avatars = AvatarFactory.generate_targeted_avatars(
        target_demographics={
            "age_range": (30, 60),
            "income_levels": ["medium", "high"],
            "required_interests": ["Health", "Fitness"]
        },
        count=6
    )
    
    # Define health supplement ads
    health_ads = [
        {
            "id": "Premium_Vitamins",
            "title": "Premium Multivitamin Complex",
            "content": """
🌟 COMPLETE WELLNESS SOLUTION 🌟

VitaMax Pro - Premium Daily Nutrition
• 50+ Essential Vitamins & Minerals
• Organic, Non-GMO Ingredients
• Third-Party Lab Tested
• Doctor Formulated
• 90-Day Supply

$89/month (Subscribe & Save 25%)
FDA-Approved Facility
30-Day Money-Back Guarantee

"I feel more energetic than ever!" - Sarah M. ⭐⭐⭐⭐⭐
"""
        },
        {
            "id": "Natural_Boost",
            "title": "Natural Energy Booster",
            "content": """
Pure Energy, Naturally

GreenBoost Daily Energy Supplement
- Organic green superfoods blend
- Natural caffeine from green tea
- No artificial stimulants
- Supports mental clarity & focus
- Vegan & gluten-free

Special Offer: $34.99 (Normally $49.99)
Try risk-free for 14 days
Join 10,000+ happy customers!
"""
        },
        {
            "id": "Science_Advanced",
            "title": "Advanced Scientific Formula", 
            "content": """
BREAKTHROUGH NUTRITIONAL SCIENCE

NutriScience Advanced Longevity Formula
→ Clinically proven ingredients
→ Anti-aging cellular support  
→ Cognitive enhancement blend
→ Metabolic optimization complex
→ Manufactured in USA

Investment in your health: $127/month
Subscription includes free health coaching
Used by leading longevity researchers
60-day satisfaction guarantee
"""
        }
    ]
    
    # Run health survey
    health_results = survey.run_ad_comparison(
        ads=health_ads, 
        avatars=health_avatars,
        context="You're interested in improving your overall health and energy levels through supplementation."
    )
    
    print(f"Health Survey Results:")
    for ad_id, stats in health_results["summary"].items():
        if ad_id != "winner":
            print(f"  {ad_id}: {stats['average_rating']:.1f}/10 avg ({stats['high_engagement']} highly engaged)")
    print(f"🏆 Winner: {health_results['summary']['winner']['ad_id']}")
    
    # Save detailed results
    survey.save_results(gaming_results, "gaming_survey_results.json")
    survey.save_results(health_results, "health_survey_results.json")
    
    print(f"\n💾 Detailed results saved:")
    print(f"  - gaming_survey_results.json")
    print(f"  - health_survey_results.json")
    
    # Demographic Analysis Example
    print(f"\n📊 Quick Demographic Analysis:")
    print("-" * 35)
    
    # Analyze gaming results by income level
    high_income_gaming = [
        eval_data for eval_data in gaming_results["individual_evaluations"]
        if any(eval["avatar_demographics"]["income_level"] == "high" 
               for eval in eval_data["evaluations"].values())
    ]
    
    print(f"Gaming Survey Insights:")
    print(f"  - Total participants: {len(gaming_avatars)}")
    print(f"  - High-income participants: {len(high_income_gaming)}")
    print(f"  - Age range: {min(a.age for a in gaming_avatars)}-{max(a.age for a in gaming_avatars)} years")
    
    print(f"\nHealth Survey Insights:")
    print(f"  - Total participants: {len(health_avatars)}")
    print(f"  - Age range: {min(a.age for a in health_avatars)}-{max(a.age for a in health_avatars)} years")
    
    return gaming_results, health_results

if __name__ == "__main__":
    main()
