def generate_design_doc(rag_chain, repo_name="this repository"):
    """Generate a comprehensive technical design document using the RAG chain."""
    prompt = f"""
You are a senior software architect and technical documentation expert. Your task is to analyze the source code of {repo_name} and generate a comprehensive, professional technical design document.

**ANALYSIS REQUIREMENTS:**
- Examine all source code files, configuration files, and project structure
- Identify programming languages, frameworks, libraries, and dependencies used
- Analyze code patterns, architectural decisions, and design principles
- Understand data flow, API endpoints, database schemas, and external integrations
- Identify security measures, error handling, and logging mechanisms

**OUTPUT FORMAT:** Generate a well-structured Markdown document with the following sections:

# 📋 Technical Design Document: {repo_name}

## 1. 🚀 Project Overview
- **Purpose**: What problem does this project solve?
- **Target Audience**: Who are the intended users?
- **Key Features**: List 3-5 main functionalities
- **Technology Stack**: Programming languages, frameworks, databases, external services
- **Project Type**: (e.g., Web API, Desktop App, Microservice, Library, etc.)

## 2. 🏗️ System Architecture

### 2.1 High-Level Architecture
- Overall system design and component interaction
- External dependencies and third-party integrations
- Data storage and persistence layer
- Authentication and authorization mechanisms

### 2.2 Low-Level Architecture
- Module/package structure and organization
- Class hierarchies and object relationships
- Design patterns implemented (e.g., MVC, Repository, Factory, etc.)
- Code organization principles and conventions

## 3. 🔧 Core Functionality

### 3.1 Main Features
- Detailed description of each major feature
- Input/output specifications
- Business logic implementation
- Error handling strategies

### 3.2 API Endpoints (if applicable)
- List all REST/GraphQL endpoints
- HTTP methods, request/response formats
- Authentication requirements
- Rate limiting and validation

### 3.3 Database Design (if applicable)
- Database type and schema design
- Entity relationships and constraints
- Indexing strategy and performance considerations

## 4. 🔗 Module Interconnections
- How different modules/components communicate
- Data flow between components
- Event-driven interactions (if any)
- Dependency injection and service location patterns

## 5. 📡 Message Queues & Communication
- Message brokers used (Kafka, RabbitMQ, Redis, etc.)
- Topic/queue structure and naming conventions
- Producer-consumer patterns
- Event sourcing or CQRS implementation (if applicable)

## 6. 🛡️ Security & Performance
- Authentication and authorization mechanisms
- Data encryption and security measures
- Performance optimization strategies
- Caching implementation
- Monitoring and logging

## 7. 🚀 Deployment & Infrastructure
- Deployment strategy and environments
- Container orchestration (Docker, Kubernetes)
- CI/CD pipeline configuration
- Infrastructure as Code (if applicable)

## 8. 📊 Technical Diagrams

### 8.1 System Architecture Diagram
```mermaid
graph TB
    %% Generate based on actual system components
    subgraph "External"
        Client[Client Applications]
        DB[(Database)]
        Cache[(Cache/Redis)]
    end
    
    subgraph "Application Layer"
        API[API Gateway/Router]
        Service[Business Logic]
        Data[Data Access Layer]
    end
    
    Client --> API
    API --> Service
    Service --> Data
    Data --> DB
    Service --> Cache
```

### 8.2 Sequence Diagram (Main User Flow)
```mermaid
sequenceDiagram
    participant User
    participant API
    participant Service
    participant Database
    
    %% Generate based on actual user interactions
    User->>API: Request
    API->>Service: Process
    Service->>Database: Query
    Database-->>Service: Response
    Service-->>API: Result
    API-->>User: Response
```

### 8.3 Class Diagram (Core Classes)
```mermaid
classDiagram
    %% Generate based on actual class structure
    class MainClass {{
        +property: type
        +method(): return_type
    }}
    
    class DependentClass {{
        +property: type
        +method(): return_type
    }}
    
    MainClass --> DependentClass
```

### 8.4 Data Flow Diagram
```mermaid
flowchart LR
    %% Generate based on actual data processing
    Input[Data Input] --> Process[Processing Logic]
    Process --> Transform[Data Transformation]
    Transform --> Output[Data Output]
    Process --> Cache[(Cache)]
    Transform --> Storage[(Storage)]
```

### 8.5 Deployment Diagram
```mermaid
graph TB
    %% Generate based on actual deployment structure
    subgraph "Production Environment"
        LB[Load Balancer]
        App1[App Instance 1]
        App2[App Instance 2]
        DB[(Production DB)]
        Cache[(Redis Cache)]
    end
    
    LB --> App1
    LB --> App2
    App1 --> DB
    App2 --> DB
    App1 --> Cache
    App2 --> Cache
```

## 9. 🔍 Code Quality & Best Practices
- Code structure and organization
- Testing strategy and coverage
- Documentation standards
- Code review and quality gates

## 10. 🚧 Future Considerations
- Scalability improvements
- Technical debt and refactoring opportunities
- Feature roadmap alignment
- Performance optimization areas

---

**IMPORTANT INSTRUCTIONS:**
1. **Be Specific**: Use actual file names, class names, function names, and technology versions found in the code
2. **Be Accurate**: Only include features and components that actually exist in the codebase
3. **Update Diagrams**: Modify the Mermaid diagrams to reflect the actual system architecture, not generic examples
4. **Use Evidence**: Reference specific code files, configuration files, or documentation when making statements
5. **Stay Current**: Focus on the current state of the code, not assumptions or possibilities
6. **Be Professional**: Use clear, concise technical language appropriate for senior developers and architects

Generate this documentation based ONLY on the actual source code provided. Do not make assumptions about features that don't exist in the codebase.
"""

    # Use invoke method for the new LangChain API
    try:
        result = rag_chain.invoke({"query": prompt})
        # Handle both old and new response formats
        if isinstance(result, dict) and "result" in result:
            return result["result"]
        return result
    except Exception as e:
        # Fallback to old run method if invoke fails
        try:
            return rag_chain.run(prompt)
        except Exception:
            raise e
