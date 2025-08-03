# Autogen Data Analyzer

An intelligent multi-agent system built with Microsoft Autogen that performs automated data analysis on CSV files. The system uses AI agents to understand natural language queries, write Python code, execute it in a secure Docker environment, and provide comprehensive data insights.

## 🎯 Project Overview

This project combines the power of large language models with secure code execution to create an automated data analysis assistant. Users can upload CSV files and ask questions in natural language, and the system will automatically generate Python code to analyze the data and provide insights.

## 🏗️ Architecture

```
├── agents/
│   ├── code_executor_agent.py    # Docker-based code execution agent
│   ├── data_analyzer_agent.py    # AI agent for data analysis logic
│   └── prompts/
│       └── data_analyzer_prompt.py  # System prompt for the analyzer
├── config/
│   ├── constants.py              # Configuration constants
│   ├── docker_utils.py           # Docker container management
│   └── model_client.py           # AI model client configuration
├── team/
│   └── analyzer_gpt_team.py      # Multi-agent team orchestration
├── temp/                         # Working directory for file processing
├── main.py                       # CLI interface
├── streamlit_app.py              # Web interface
└── requirements.txt              # Dependencies
```

## ✨ Key Features

- **Natural Language Queries**: Ask questions about your data in plain English
- **Automated Code Generation**: AI generates Python code to answer your questions
- **Secure Execution**: Code runs in isolated Docker containers
- **Multi-Agent Collaboration**: Specialized agents work together for optimal results
- **Web Interface**: User-friendly Streamlit interface for easy interaction
- **Visualization Support**: Automatic chart and graph generation with matplotlib
- **Multiple Model Support**: Compatible with OpenAI, Gemini, and other LLM providers
- **Error Handling**: Robust error detection and code correction capabilities

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Docker installed and running
- API key for your chosen LLM provider (OpenAI, Gemini, etc.)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Autogen/Data Analyzer"
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   # or
   OPENAI_API_KEY=your_openai_api_key_here
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

4. **Configure the model**
   Edit `config/constants.py` to choose your preferred model:
   ```python
   MODEL = "gemini-2.0-flash"  # or "gpt-4o", "deepseek/deepseek-r1-0528:free"
   ```

## 💻 Usage

### Web Interface (Recommended)

1. **Start the Streamlit app**
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Upload your CSV file** through the web interface

3. **Ask questions** like:
   - "Show me a summary of the data"
   - "Create a bar chart of sales by month"
   - "What are the top 10 customers by revenue?"
   - "Find correlations between different columns"

### Command Line Interface

1. **Place your CSV file** in the `temp/` directory as `data.csv`

2. **Run the analyzer**
   ```bash
   python main.py
   ```

3. **Modify the task** in `main.py`:
   ```python
   task = 'Your analysis question here'
   ```

## 🤖 Agent System

### Data Analyzer Agent
- **Role**: Understands user queries and generates Python code
- **Capabilities**: 
  - Data analysis planning
  - Python code generation
  - Result interpretation
  - Insight generation

### Code Executor Agent
- **Role**: Executes Python code in secure Docker containers
- **Features**:
  - Isolated execution environment
  - Package installation capabilities
  - Output capture and error handling
  - File system access for data processing

### Team Orchestration
- **SelectorGroupChat**: Intelligent agent selection based on task requirements
- **Termination Control**: Automatic stopping when analysis is complete
- **Context Preservation**: Maintains conversation state across interactions

## 📊 Supported Analysis Types

- **Descriptive Statistics**: Mean, median, mode, standard deviation
- **Data Visualization**: Bar charts, line plots, histograms, scatter plots
- **Correlation Analysis**: Relationship identification between variables
- **Grouping and Aggregation**: Sum, count, average by categories
- **Filtering and Sorting**: Data subset analysis
- **Missing Data Analysis**: Identification and handling of null values
- **Custom Analysis**: Any analysis expressible in Python/pandas

## 🛠️ Configuration Options

### Model Configuration
```python
# In config/constants.py
MODEL = 'gemini-2.0-flash'  # Choose your model
MAX_TURNS = 15              # Maximum conversation turns
DOCKER_TIMEOUT = 120        # Code execution timeout (seconds)
```

### Docker Configuration
```python
# In config/docker_utils.py
image = 'amancevice/pandas'  # Docker image with pandas pre-installed
work_dir = 'temp'            # Working directory in container
timeout = 120                # Execution timeout
```

## 📝 Example Queries

### Basic Data Exploration
```
"What does this dataset look like?"
"Show me the first 10 rows"
"What are the column names and data types?"
```

### Statistical Analysis
```
"Calculate basic statistics for all numeric columns"
"Find the correlation between age and income"
"What's the distribution of the target variable?"
```

### Visualization
```
"Create a histogram of the age column"
"Show me a bar chart of categories by count"
"Generate a scatter plot of price vs quantity"
```

### Advanced Analysis
```
"Find outliers in the dataset"
"Perform clustering analysis on the data"
"Create a correlation heatmap"
```

## 🔧 Advanced Features

### Custom Prompts
Modify the system prompt in `agents/prompts/data_analyzer_prompt.py` to customize the agent's behavior:

```python
DATA_ANALYZER_PROMPT = """
Your custom instructions here...
"""
```

### Multiple File Support
The system can be extended to handle multiple CSV files by modifying the file handling logic in the agents.

### Export Capabilities
Generated visualizations are automatically saved as `output.png` in the `temp/` directory and displayed in the web interface.

## 🐳 Docker Environment

The system uses a containerized execution environment for security:

- **Base Image**: `amancevice/pandas` (includes pandas, numpy, matplotlib)
- **Additional Packages**: Automatically installed via pip when needed
- **Isolation**: Complete isolation from host system
- **Resource Limits**: Configurable timeout and resource constraints

## 🚨 Error Handling

The system includes comprehensive error handling:

- **Code Errors**: Automatic detection and correction of Python syntax errors
- **Package Issues**: Automatic installation of missing libraries
- **Data Issues**: Graceful handling of malformed data
- **Timeout Management**: Prevents infinite loops and long-running processes

## 📈 Performance Optimization

- **Caching**: Model responses can be cached for repeated queries
- **Parallel Processing**: Multiple agents can work simultaneously
- **Resource Management**: Docker containers are properly started and stopped
- **Memory Efficiency**: Large datasets are processed in chunks when necessary

## 🔒 Security Features

- **Sandboxed Execution**: All code runs in isolated Docker containers
- **No Host Access**: Containers cannot access the host file system
- **Timeout Protection**: Prevents resource exhaustion
- **Input Validation**: Queries are validated before processing

## 🧪 Testing

Run the system with the included Titanic dataset:

```bash
# The temp/data.csv contains Titanic passenger data
python main.py
```

Example queries for the Titanic dataset:
- "How many passengers survived vs died?"
- "Create a visualization of survival rates by passenger class"
- "What's the correlation between age and survival?"

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📋 Requirements

```txt
autogen-agentchat
autogen-core
autogen-ext
asyncio
streamlit
openai
python-dotenv
tiktoken
autogen-ext[docker]
autogen-ext[openai]
autogen-ext[ollama]
```

## 🐛 Troubleshooting

### Common Issues

**Docker not starting**
```bash
# Ensure Docker is running
docker --version
sudo systemctl start docker  # Linux
```

**API Key issues**
```bash
# Check your .env file
cat .env
# Ensure the correct API key constant is used in config/constants.py
```

**Package installation errors**
```bash
# Update pip and reinstall requirements
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Debug Mode

Enable detailed logging by modifying the constants:

```python
DEBUG = True
MAX_TURNS = 50  # For complex analyses
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Microsoft Autogen** for the multi-agent framework
- **Docker Community** for containerization tools
- **Streamlit** for the web interface framework
- **Pandas/Matplotlib** for data analysis and visualization capabilities

---

**Note**: Ensure Docker is running before starting the application. The system requires an active internet connection for AI model API calls and Docker image downloads.
