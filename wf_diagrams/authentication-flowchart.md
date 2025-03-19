# Authentication Flowchart

```mermaid
flowchart TD
    subgraph Client["Client Applications"]
        MApp["Mobile App"] --> Auth["Authentication Requests"]
        WApp["Web App"] --> Auth
        API["API Clients"] --> Auth
    end

    subgraph AuthService["Authentication Service"]
        Auth --> Login["Login Endpoint<br>/auth/login"]
        Auth --> Register["Registration Endpoint<br>/auth/register"]
        Auth --> Refresh["Token Refresh<br>/auth/refresh"]
        Auth --> Reset["Password Reset<br>/auth/reset-password"]
        
        Login & Register & Reset --> Val["Validation Layer<br>(Pydantic Schemas)"]
        Val --> SEC["Security Layer"]
        
        SEC --> Hash["Password Hashing<br>(Bcrypt)"]
        SEC --> JWT["JWT Generation<br>(PyJWT)"]
        
        JWT --> Claims["JWT Claims:<br>- user_id<br>- business_id<br>- role<br>- permissions<br>- exp time"]
        
        subgraph Redis["Redis Cache (Optional)"]
            Blacklist["Token Blacklist"]
            UserSessions["Active Sessions"]
        end
        
        JWT -.-> Redis
        Refresh --> JWT
        Refresh -.-> Redis
    end
    
    subgraph DBLayer["Database Integration"]
        SEC --> UserDB[(Users Table)]
        SEC --> BusinessDB[(Businesses Table)]
        SEC --> RoleDB[(Roles & Permissions)]
    end
    
    subgraph Middleware["Auth Middleware"]
        APISec["API Security<br>Dependency"] --> Verify["JWT Verification"]
        APISec --> Extract["Extract User Info"]
        APISec --> CheckPerm["Check Permissions"]
        
        Verify -.-> Redis
        Extract --> UserLookup["User Lookup<br>(Optional)"]
        UserLookup -.-> DBLayer
    end
    
    JWT --> TokenResp["Response:<br>- access_token<br>- refresh_token<br>- token_type<br>- expires_in"]
    TokenResp --> Client
    
    Middleware --> Protected["Protected<br>Resources"]
