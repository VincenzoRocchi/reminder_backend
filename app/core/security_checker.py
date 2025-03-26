"""
Security Checker Module

This module performs security checks on application configuration 
to ensure security best practices are followed.
"""

import logging
import re
from typing import List, Dict, Any, Optional
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class SecurityChecker:
    """
    Security checker for validating security settings and credentials.
    """
    
    def __init__(self, settings=None):
        """Initialize with optional settings object"""
        self.settings = settings
        self.issues = []
        self.critical_issues = []
        self.warnings = []
    
    def check_env_files(self, env_files: List[str] = None) -> Dict[str, List[str]]:
        """
        Check environment files for potential security issues
        """
        if env_files is None:
            env_files = [
                ".env", 
                ".env.development", 
                ".env.testing", 
                ".env.production"
            ]
        
        results = {"errors": [], "warnings": []}
        
        for env_file in env_files:
            # Skip if file doesn't exist
            if not Path(env_file).exists():
                continue
                
            logger.info(f"Checking security of {env_file}")
            
            with open(env_file, 'r') as f:
                content = f.read()
                
            # Check for sensitive credentials
            sensitive_patterns = {
                "SECRET_KEY": r'SECRET_KEY=(.+)',
                "DB_PASSWORD": r'DB_PASSWORD=(.+)',
                "SMTP_PASSWORD": r'SMTP_PASSWORD=(.+)',
                "TWILIO_AUTH_TOKEN": r'TWILIO_AUTH_TOKEN=(.+)',
                "REDIS_PASSWORD": r'REDIS_PASSWORD=(.+)',
                "API_KEY": r'.*API_KEY=(.+)'
            }
            
            for key, pattern in sensitive_patterns.items():
                matches = re.findall(pattern, content)
                for match in matches:
                    # Skip empty values or placeholders
                    if not match or match == '""' or match == "''":
                        continue
                        
                    # Check if it's a default/weak value
                    if self._is_default_or_weak_value(match):
                        if env_file == '.env.production':
                            issue = f"Critical: {key} in {env_file} appears to be a default/weak value"
                            results["errors"].append(issue)
                        else:
                            issue = f"Warning: {key} in {env_file} appears to be a default/weak value"
                            results["warnings"].append(issue)
        
        # Check if production is using proper SSL for database
        if '.env.production' in env_files and Path('.env.production').exists():
            with open('.env.production', 'r') as f:
                content = f.read()
                
            if 'SQLALCHEMY_DATABASE_URI' in content and 'mysql' in content and 'ssl=true' not in content:
                issue = "Critical: Production database connection should use SSL"
                results["errors"].append(issue)
        
        return results
    
    def check_service_credentials(self) -> Dict[str, List[str]]:
        """
        Check service credentials configuration
        """
        if not self.settings:
            return {"errors": ["Settings object not provided"], "warnings": []}
            
        results = {"errors": [], "warnings": []}
        
        # Check Twilio credentials
        if self.settings.ENV == "production":
            if not self.settings.TWILIO_ACCOUNT_SID or len(self.settings.TWILIO_ACCOUNT_SID) < 10:
                results["errors"].append("Production Twilio Account SID not properly configured")
                
            if not self.settings.TWILIO_AUTH_TOKEN or len(self.settings.TWILIO_AUTH_TOKEN) < 10:
                results["errors"].append("Production Twilio Auth Token not properly configured")
                
            if not self.settings.SMTP_HOST or self.settings.SMTP_HOST == "localhost":
                results["warnings"].append("Production SMTP host should not be localhost")
                
        # Add more service credential checks as needed
                
        return results
    
    def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all security checks and return results
        """
        env_results = self.check_env_files()
        
        credential_results = {"errors": [], "warnings": []}
        if self.settings:
            credential_results = self.check_service_credentials()
        
        return {
            "env_files": env_results,
            "service_credentials": credential_results,
            "total_errors": len(env_results["errors"]) + len(credential_results["errors"]),
            "total_warnings": len(env_results["warnings"]) + len(credential_results["warnings"])
        }
    
    def _is_default_or_weak_value(self, value: str) -> bool:
        """
        Check if a value appears to be a default or weak value
        """
        # Remove quotes if present
        value = value.strip('"\'')
        
        # Default/weak value patterns
        weak_patterns = [
            r'your[-_].*[-_]here',
            r'default[-_].*',
            r'change[-_].*',
            r'test[-_].*',
            r'secret[-_]key',
            r'password',
            r'123',
            r'example'
        ]
        
        # Check length for likely weak values
        if len(value) < 8:
            return True
            
        # Check against patterns
        for pattern in weak_patterns:
            if re.search(pattern, value.lower()):
                return True
                
        return False


def check_security_at_startup(settings):
    """
    Run security checks at application startup
    """
    checker = SecurityChecker(settings)
    results = checker.run_all_checks()
    
    if results["total_errors"] > 0:
        logger.critical(f"Security check found {results['total_errors']} critical issues")
        
    if results["total_warnings"] > 0:
        logger.warning(f"Security check found {results['total_warnings']} security warnings")
        
    # Log detailed results at info level
    for error in results["env_files"]["errors"] + results["service_credentials"]["errors"]:
        logger.error(f"Security issue: {error}")
        
    for warning in results["env_files"]["warnings"] + results["service_credentials"]["warnings"]:
        logger.warning(f"Security warning: {warning}")
        
    return results 