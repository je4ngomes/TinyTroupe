#!/usr/bin/env python3
"""
Minimal Avatar Survey System
A lightweight implementation inspired by TinyTroupe for simulating user avatars
and conducting marketing/ad review surveys.
"""

import json
import os
import random
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

@dataclass
class UserAvatar:
    """Represents a simulated user persona for marketing surveys."""
    name: str
    age: int
    occupation: str
    income_level: str  # "low", "medium", "high"
    interests: List[str]
    personality_traits: List[str]
    tech_savviness: str  # "low", "medium", "high"
    shopping_behavior: str  # "budget-conscious", "impulse", "research-heavy", "brand-loyal"
    
    def to_prompt_context(self) -> str:
        """Convert avatar to context for LLM prompts."""
        return f"""
You are {self.name}, a {self.age}-year-old {self.occupation}.
Your income level is {self.income_level}.
Your interests include: {', '.join(self.interests)}.
Your personality traits: {', '.join(self.personality_traits)}.
Your tech savviness is {self.tech_savviness}.
Your shopping behavior is {self.shopping_behavior}.

Respond authentically based on this persona.
"""

class AvatarFactory:
    """Factory for generating diverse user avatars."""
    
    OCCUPATIONS = [
        "Software Engineer", "Teacher", "Nurse", "Marketing Manager", 
        "Student", "Retired", "Small Business Owner", "Artist", "Accountant",
        "Chef", "Doctor", "Sales Representative", "Designer", "Writer"
    ]
    
    INTERESTS = [
        "Technology", "Sports", "Travel", "Cooking", "Reading", "Music",
        "Movies", "Gaming", "Fitness", "Art", "Fashion", "Photography",
        "Gardening", "Cars", "Finance", "Health", "Nature", "Social Media"
    ]
    
    PERSONALITY_TRAITS = [
        "Outgoing", "Analytical", "Creative", "Practical", "Curious",
        "Cautious", "Adventurous", "Traditional", "Modern", "Frugal",
        "Generous", "Detail-oriented", "Big-picture thinker", "Social",
        "Independent", "Family-oriented", "Career-focused", "Relaxed"
    ]
    
    @staticmethod
    def generate_random_avatar() -> UserAvatar:
        """Generate a random user avatar."""
        name = f"User_{random.randint(1000, 9999)}"
        age = random.randint(18, 70)
        occupation = random.choice(AvatarFactory.OCCUPATIONS)
        income_level = random.choice(["low", "medium", "high"])
        interests = random.sample(AvatarFactory.INTERESTS, k=random.randint(3, 6))
        personality_traits = random.sample(AvatarFactory.PERSONALITY_TRAITS, k=random.randint(2, 4))
        tech_savviness = random.choice(["low", "medium", "high"])
        shopping_behavior = random.choice(["budget-conscious", "impulse", "research-heavy", "brand-loyal"])
        
        return UserAvatar(
            name=name,
            age=age,
            occupation=occupation,
            income_level=income_level,
            interests=interests,
            personality_traits=personality_traits,
            tech_savviness=tech_savviness,
            shopping_behavior=shopping_behavior
        )
    
    @staticmethod
    def generate_targeted_avatars(target_demographics: Dict[str, Any], count: int = 10) -> List[UserAvatar]:
        """Generate avatars matching specific demographics."""
        avatars = []
        for i in range(count):
            avatar = AvatarFactory.generate_random_avatar()
            
            # Apply target demographics constraints
            if "age_range" in target_demographics:
                min_age, max_age = target_demographics["age_range"]
                avatar.age = random.randint(min_age, max_age)
            
            if "income_levels" in target_demographics:
                avatar.income_level = random.choice(target_demographics["income_levels"])
            
            if "required_interests" in target_demographics:
                # Ensure at least one required interest is included
                required = random.choice(target_demographics["required_interests"])
                if required not in avatar.interests:
                    avatar.interests.append(required)
            
            avatars.append(avatar)
        
        return avatars

class AdEvaluator:
    """Handles ad evaluation by avatars using LLM."""
    
    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model
        self.client = None
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY") and OpenAI is not None:
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def evaluate_ad(self, avatar: UserAvatar, ad_content: str, context: str = "") -> Dict[str, Any]:
        """Have an avatar evaluate an advertisement."""
        
        prompt = f"""
{avatar.to_prompt_context()}

{context}

Please evaluate the following advertisement:

{ad_content}

Respond with your honest opinion as {avatar.name}. Consider:
1. How appealing is this ad to you personally?
2. Would you be likely to click on or engage with this ad?
3. What specifically draws your attention (or doesn't)?
4. Any concerns or negative reactions?

Rate your likelihood to engage on a scale of 1-10 and explain your reasoning.
Be authentic to your persona - consider your interests, income level, and shopping behavior.
"""
        
        if not self.client:
            # Return mock response if OpenAI is not available
            rating = random.randint(4, 8)
            return {
                "avatar_name": avatar.name,
                "rating": rating,
                "evaluation": f"Mock evaluation from {avatar.name} - Rating: {rating}/10 (OpenAI not available)",
                "avatar_demographics": asdict(avatar)
            }
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            
            evaluation_text = response.choices[0].message.content
            
            # Extract rating (simple regex approach)
            import re
            rating_match = re.search(r'(\d+)(?:/10|\.0)?', evaluation_text)
            rating = int(rating_match.group(1)) if rating_match else 5
            
            return {
                "avatar_name": avatar.name,
                "rating": rating,
                "evaluation": evaluation_text,
                "avatar_demographics": asdict(avatar)
            }
            
        except Exception as e:
            return {
                "avatar_name": avatar.name,
                "rating": 0,
                "evaluation": f"Error in evaluation: {str(e)}",
                "avatar_demographics": asdict(avatar)
            }

class SurveyRunner:
    """Orchestrates survey campaigns with multiple avatars and ads."""
    
    def __init__(self, evaluator: AdEvaluator):
        self.evaluator = evaluator
        self.results = []
    
    def run_ad_comparison(self, ads: List[Dict[str, str]], avatars: List[UserAvatar],
                         context: str = "") -> Dict[str, Any]:
        """Run a comparison survey between multiple ads."""
        
        results = {
            "ads": ads,
            "total_avatars": len(avatars),
            "individual_evaluations": [],
            "summary": {}
        }
        
        # Collect individual evaluations
        for i, avatar in enumerate(avatars):
            print(f"Evaluating with avatar {i+1}/{len(avatars)}: {avatar.name}")
            
            avatar_results = {}
            for j, ad in enumerate(ads):
                ad_id = ad.get("id", f"Ad_{j+1}")
                evaluation = self.evaluator.evaluate_ad(
                    avatar=avatar,
                    ad_content=ad["content"],
                    context=context
                )
                avatar_results[ad_id] = evaluation
            
            results["individual_evaluations"].append({
                "avatar": avatar.name,
                "evaluations": avatar_results
            })
        
        # Generate summary
        results["summary"] = self._generate_summary(results["individual_evaluations"], ads)
        
        return results
    
    def _generate_summary(self, evaluations: List[Dict], ads: List[Dict]) -> Dict[str, Any]:
        """Generate summary statistics from evaluations."""
        
        ad_ratings = {}
        for ad in ads:
            ad_id = ad.get("id", f"Ad_{ads.index(ad)+1}")
            ad_ratings[ad_id] = []
        
        # Collect all ratings
        for eval_data in evaluations:
            for ad_id, evaluation in eval_data["evaluations"].items():
                ad_ratings[ad_id].append(evaluation["rating"])
        
        # Calculate statistics
        summary = {}
        for ad_id, ratings in ad_ratings.items():
            if ratings:
                summary[ad_id] = {
                    "average_rating": sum(ratings) / len(ratings),
                    "total_responses": len(ratings),
                    "high_engagement": len([r for r in ratings if r >= 7]),
                    "low_engagement": len([r for r in ratings if r <= 4])
                }
        
        # Determine winner
        if summary:
            winner = max(summary.items(), key=lambda x: x[1]["average_rating"])
            summary["winner"] = {
                "ad_id": winner[0],
                "average_rating": winner[1]["average_rating"]
            }
        
        return summary
    
    def save_results(self, results: Dict[str, Any], filename: str):
        """Save survey results to JSON file."""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Results saved to {filename}")

def create_sample_ads() -> List[Dict[str, str]]:
    """Create sample ads for testing."""
    return [
        {
            "id": "Ad_A",
            "title": "Premium Fitness Tracker",
            "content": """
🏃‍♀️ Transform Your Health Journey! 🏃‍♀️

NEW FitTrack Pro - Advanced Fitness Tracker
✅ 24/7 Heart Rate Monitoring
✅ Sleep Quality Analysis  
✅ 30+ Workout Modes
✅ 7-Day Battery Life

Limited Time: 40% OFF + FREE Shipping!
$199 $119 - Order Now!

"Best fitness tracker I've ever used!" ⭐⭐⭐⭐⭐
"""
        },
        {
            "id": "Ad_B", 
            "title": "Budget Fitness Watch",
            "content": """
Smart Fitness Watch - Affordable Health Tracking

Track your steps, heart rate, and sleep
Water resistant design
Compatible with all smartphones
30-day money back guarantee

Only $39.99 - Free shipping on orders over $35
Get yours today and start your fitness journey!
"""
        },
        {
            "id": "Ad_C",
            "title": "Luxury Health Monitor", 
            "content": """
EliteHealth Pro - The Ultimate Wellness Companion

Professional-grade health monitoring
FDA-approved sensors
Personalized AI coaching
Integration with healthcare providers
Premium titanium construction

Investment in your health: $599
Financing available - $25/month
Trusted by healthcare professionals worldwide
"""
        }
    ]

def main():
    """Main function demonstrating the avatar survey system."""
    
    print("🤖 Minimal Avatar Survey System Demo")
    print("=" * 50)
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY environment variable not set.")
        print("This demo will use mock responses instead of real LLM evaluation.")
        print()

    # Create evaluator and survey runner
    evaluator = AdEvaluator()
    survey = SurveyRunner(evaluator)
    
    # Generate diverse avatars
    print("👥 Generating user avatars...")
    avatars = AvatarFactory.generate_targeted_avatars(
        target_demographics={
            "age_range": (25, 55),
            "income_levels": ["medium", "high"],
            "required_interests": ["Fitness", "Technology", "Health"]
        },
        count=5
    )

    for avatar in avatars:
        print(f"  - {avatar.name}: {avatar.age}yo {avatar.occupation}, "
              f"{avatar.income_level} income, likes {', '.join(avatar.interests[:3])}")
    
    # Create sample ads
    print("\n📢 Creating sample advertisements...")
    ads = create_sample_ads()
    for ad in ads:
        print(f"  - {ad['id']}: {ad['title']}")
    
    # Run survey
    print("\n🔄 Running ad evaluation survey...")
    context = "You are looking for a fitness tracker to help monitor your health and workouts."
    
    if os.getenv("OPENAI_API_KEY"):
        # Real evaluation with OpenAI
        results = survey.run_ad_comparison(ads, avatars, context)
    else:
        # Mock results for demo
        print("Using mock responses (set OPENAI_API_KEY for real evaluation)")
        results = create_mock_results(ads, avatars)

    # Display results
    print("\n📊 Survey Results Summary:")
    print("-" * 30)
    
    for ad_id, stats in results["summary"].items():
        if ad_id != "winner":
            print(f"{ad_id}: Avg Rating {stats['average_rating']:.1f}/10 "
                  f"({stats['high_engagement']} high engagement)")
    
    if "winner" in results["summary"]:
        winner = results["summary"]["winner"]
        print(f"\n🏆 Winner: {winner['ad_id']} (Rating: {winner['average_rating']:.1f}/10)")
    
    # Save results
    survey.save_results(results, "survey_results.json")
    print(f"\n✅ Complete results saved to survey_results.json")
    
    return results

def create_mock_results(ads: List[Dict[str, str]], avatars: List[UserAvatar]) -> Dict[str, Any]:
    """Create mock survey results for demo purposes."""
    results = {
        "ads": ads,
        "total_avatars": len(avatars),
        "individual_evaluations": [],
        "summary": {}
    }
    
    # Generate mock evaluations
    for avatar in avatars:
        avatar_results = {}
        for ad in ads:
            ad_id = ad.get("id", f"Ad_{ads.index(ad)+1}")
            
            # Simulate rating based on avatar characteristics
            base_rating = random.randint(4, 8)
            if avatar.income_level == "high" and "Luxury" in ad["title"]:
                base_rating += 2
            elif avatar.income_level == "low" and "Budget" in ad["title"]:
                base_rating += 1
            
            rating = min(10, max(1, base_rating))
            
            avatar_results[ad_id] = {
                "avatar_name": avatar.name,
                "rating": rating,
                "evaluation": f"Mock evaluation from {avatar.name} - Rating: {rating}/10",
                "avatar_demographics": asdict(avatar)
            }
        
        results["individual_evaluations"].append({
            "avatar": avatar.name,
            "evaluations": avatar_results
        })
    
    # Generate mock summary
    ad_ratings = {}
    for ad in ads:
        ad_id = ad.get("id", f"Ad_{ads.index(ad)+1}")
        ratings = [eval_data["evaluations"][ad_id]["rating"] 
                  for eval_data in results["individual_evaluations"]]
        
        ad_ratings[ad_id] = {
            "average_rating": sum(ratings) / len(ratings),
            "total_responses": len(ratings),
            "high_engagement": len([r for r in ratings if r >= 7]),
            "low_engagement": len([r for r in ratings if r <= 4])
        }
    
    winner = max(ad_ratings.items(), key=lambda x: x[1]["average_rating"])
    ad_ratings["winner"] = {
        "ad_id": winner[0],
        "average_rating": winner[1]["average_rating"]
    }
    
    results["summary"] = ad_ratings
    return results

if __name__ == "__main__":
    main()
