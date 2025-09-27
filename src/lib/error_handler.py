import logging

def setup_logging():
    """
    Sets up the logging configuration for the application.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

class McpStoryServiceError(Exception):
    """
    Base exception for the MCP Story Service.
    """
    def __init__(self, message: str, confidence_impact: float = 0.0):
        self.message = message
        self.confidence_impact = confidence_impact
        super().__init__(self.message)

class IntegrationError(McpStoryServiceError):
    """
    Exception raised for errors during integration with external services.
    """
    def __init__(self, service_name: str, message: str, confidence_impact: float = 0.1):
        self.service_name = service_name
        super().__init__(f"Error integrating with {service_name}: {message}", confidence_impact)

class AnalysisError(McpStoryServiceError):
    """
    Exception raised for errors during story analysis.
    """
    def __init__(self, message: str, confidence_impact: float = 0.05):
        super().__init__(f"Analysis error: {message}", confidence_impact)
