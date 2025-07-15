# Minimal Avatar Survey System

A lightweight, dynamic, and modular system for simulating user avatars and conducting marketing/ad review surveys. Inspired by Microsoft's TinyTroupe but simplified for focused marketing research use cases.

## Features

- **Dynamic Avatar Generation**: Create diverse user personas with configurable demographics
- **Targeted Demographics**: Generate avatars matching specific criteria (age, income, interests)
- **Ad Evaluation**: Test multiple advertisements against simulated user personas
- **Automated Analysis**: Get summary statistics and determine winning ads
- **Flexible & Modular**: Easy to extend and customize for different use cases
- **Mock Mode**: Works without OpenAI API for testing and development

## Quick Start

### Installation

1. Clone or download the system:
```bash
git clone <repository-url>
cd minimal-avatar-survey
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Set up OpenAI API key for real evaluations:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Basic Usage

Run the demo:
```bash
python minimal_avatar_survey.py
```

This will:
1. Generate 5 diverse user avatars
2. Create 3 sample fitness tracker ads
3. Have each avatar evaluate all ads
4. Show summary results and determine the winning ad

### Custom Usage

```python
from minimal_avatar_survey import AvatarFactory, AdEvaluator, SurveyRunner

# Create targeted avatars
avatars = AvatarFactory.generate_targeted_avatars(
    target_demographics={
        "age_range": (25, 45),
        "income_levels": ["medium", "high"],
        "required_interests": ["Technology", "Gaming"]
    },
    count=10
)

# Define your ads
ads = [
    {
        "id": "Ad_1",
        "title": "Gaming Laptop",
        "content": "High-performance gaming laptop with RTX 4080..."
    },
    {
        "id": "Ad_2", 
        "title": "Budget Gaming PC",
        "content": "Affordable gaming desktop for casual gamers..."
    }
]

# Run survey
evaluator = AdEvaluator()
survey = SurveyRunner(evaluator)

results = survey.run_ad_comparison(
    ads=ads,
    avatars=avatars,
    context="You're looking to upgrade your gaming setup"
)

# View results
print(f"Winner: {results['summary']['winner']['ad_id']}")
survey.save_results(results, "my_survey_results.json")
```

## Key Components

### UserAvatar
Represents a simulated user with:
- Demographics (age, occupation, income)
- Interests and personality traits
- Shopping behavior patterns
- Tech savviness level

### AvatarFactory
Generates diverse avatars with:
- Random generation for broad testing
- Targeted generation for specific demographics
- Configurable constraints and requirements

### AdEvaluator
Evaluates ads using:
- LLM-powered persona simulation (if OpenAI available)
- Structured prompts for consistent evaluation
- Automatic rating extraction from responses
- Fallback to mock responses for development

### SurveyRunner
Orchestrates surveys with:
- Multi-ad comparison capabilities
- Statistical summary generation
- Result export to JSON
- Progress tracking and reporting

## Output Format

Survey results include:
- Individual avatar evaluations with ratings (1-10)
- Demographic breakdown of responses
- Summary statistics (average ratings, engagement levels)
- Winner determination
- Complete response data for further analysis

## Use Cases

- **A/B Testing**: Compare multiple ad variations
- **Demographic Targeting**: Test ads against specific user segments  
- **Market Research**: Understand appeal across different personas
- **Creative Optimization**: Identify effective messaging and design elements
- **Budget Planning**: Focus spending on highest-performing ads

## Limitations

- Simulated responses may not perfectly match real user behavior
- Requires OpenAI API for realistic evaluations (falls back to mock responses)
- Simple rating extraction may miss nuanced feedback
- Limited to text-based ad content (no image analysis)

## Extending the System

The modular design makes it easy to:
- Add new avatar characteristics
- Implement different evaluation metrics
- Support additional ad formats
- Integrate with external data sources
- Add more sophisticated analysis

## Dependencies

- Python 3.7+
- `openai` (for LLM evaluation)
- `python-dotenv` (for environment variables)

## License

This project is provided as-is for educational and research purposes.
