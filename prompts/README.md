# Prompts Directory

This directory contains system prompts and training examples for OpenAI FAQ generation.

## Directory Structure

```
prompts/
├── system_prompts/      # Complete system prompts (one per use case)
├── training_examples/   # Writing style examples for training
└── README.md           # This file
```

## System Prompts (`system_prompts/`)

This directory contains **complete system prompts** that OpenAI will use when generating FAQ responses. Each file represents a different use case.

### File Format

Each file should contain the complete system prompt text. You can use `{examples}` as a placeholder that will be automatically replaced with training examples when the prompt is loaded.

### Usage

- The `default.txt` file will be used if no specific prompt is selected
- Create additional files like `customer_service.txt`, `sales_inquiry.txt`, etc. for different use cases
- Files are loaded by name (without the .txt extension)

## Training Examples (`training_examples/`)

This directory contains writing style examples that are used to train the model on your preferred writing style.

### File Format

Each file should contain a complete example in the following format:

```
Example X:
User Input: "Your example user question here"
Bot Response: "Your example bot response instruction"

Your Generated Prompt:
Your example of how the prompt should be written in your desired style.
```

### Adding New Examples

Simply create a new `.txt` file in the `training_examples/` directory. The system will automatically load all `.txt` files and include them in the training examples.

