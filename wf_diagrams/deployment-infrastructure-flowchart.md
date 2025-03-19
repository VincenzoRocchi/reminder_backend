# claude-flowchart-mixandmatch Flowchart

```mermaid
flowchart TD
    subgraph DeveloperWorkflow["Developer Workflow"]
        DevEnv["Development<br>Environment"] --> GitRepo["Git Repository"]
        GitRepo --> PRProcess["Pull Request<br>Process"]
        PRProcess --> CodeReview["Code Review"]
        CodeReview --> CITrigger["CI Trigger"]
    end
    
    subgraph CIPipeline["CI Pipeline"]
        CITrigger --> CodeLinting["Code Linting"]
        CodeLinting --> UnitTests["Unit Tests"]
        UnitTests --> IntegrationTests["Integration Tests"]
        IntegrationTests --> SecurityScan["Security Scanning"]
        SecurityScan --> BuildArtifact["Build Artifact"]
        BuildArtifact --> DockerImage["Docker Image<br>Creation"]
        DockerImage --> ImagePush["Push to Container<br>Registry"]
    end
    
    subgraph CDPipeline["CD Pipeline"]
        ImagePush --> StagingDeploy["Deploy to<br>Staging"]
        StagingDeploy --> StagingTests["Staging<br>Environment Tests"]
        StagingTests --> ApprovalGate["Deployment<br>Approval Gate"]
        ApprovalGate --> ProductionDeploy["Deploy to<br>Production"]
        ProductionDeploy --> SmokeTests["Production<br>Smoke Tests"]
        
        RollbackPlan["Rollback Plan"] -.-> ProductionDeploy
    end
    
    subgraph AWSInfrastructure["AWS Infrastructure"]
        subgraph NetworkLayer["Network Layer"]
            VPC["Virtual Private<br>Cloud (VPC)"] --> PublicSubnets["Public Subnets"]
            VPC --> PrivateSubnets["Private Subnets"]
            InternetGateway["Internet Gateway"] --> PublicSubnets
            PublicSubnets --> NAT["NAT Gateway"]
            NAT --> PrivateSubnets
            
            SecurityGroups["Security Groups"] --> NetworkACLs["Network ACLs"]
        end
        
        subgraph ComputeLayer["Compute Layer"]
            ALB["Application Load<br>Balancer"] --> ASG["Auto Scaling<br>Group"]
            ASG --> EC2["EC2 Instances"]
            
            ASG --> ECS["ECS Cluster<br>(Alternative)"]
            ECS --> Containers["Docker Containers"]
            
            Lambda["AWS Lambda<br>(For specific tasks)"]
        end
        
        subgraph DataLayer["Data Layer"]
            RDS["RDS MySQL<br>Primary"] --> RDSRead["RDS Read<br>Replicas"]
            RDS --> DBBackup["Automated<br>Backups"]
            
            ElastiCache["Redis<br>ElastiCache"] --> CacheNodes["Cache Cluster<br>Nodes"]
            
            S3["S3 Buckets"] --> LifecycleRules["S3 Lifecycle<br>Rules"]
        end
        
        subgraph MessagingLayer["Messaging Layer"]
            SQS["SQS Queues"] --> DLQ["Dead Letter<br>Queues"]
            SNS["SNS Topics"] --> Subscribers["Topic<br>Subscribers"]
        end
        
        subgraph MonitoringLayer["Monitoring Layer"]
            CloudWatch["CloudWatch"] --> LogGroups["Log Groups"]
            CloudWatch --> Alarms["CloudWatch<br>Alarms"]
            CloudWatch --> Dashboards["Monitoring<br>Dashboards"]
            
            XRay["AWS X-Ray"] --> TraceAnalysis["Trace Analysis"]
        end
        
        subgraph SecurityLayer["Security Layer"]
            IAM["IAM Roles &<br>Policies"] --> ResourceAccess["Resource Access<br>Control"]
            KMS["KMS Keys"] --> DataEncryption["Data Encryption"]
            WAF["AWS WAF"] --> ALB
        end
    end
    
    subgraph DisasterRecovery["Disaster Recovery"]
        BackupStrategy["Backup Strategy"] --> RegularBackups["Regular Backups"]
        MultiRegion["Multi-Region<br>Strategy"] --> RegionFailover["Region Failover<br>Plan"]
        RPO["Recovery Point<br>Objective (RPO)"] --> RTO["Recovery Time<br>Objective (RTO)"]
    end
    
    subgraph ScalingStrategy["Scaling Strategy"]
        AutoScaling["Auto Scaling<br>Policies"] --> ScaleOut["Scale Out<br>Triggers"]
        AutoScaling --> ScaleIn["Scale In<br>Triggers"]
        
        DatabaseScaling["Database<br>Scaling"] --> ReadScaling["Read Scaling<br>Strategy"]
        DatabaseScaling --> WriteScaling["Write Scaling<br>Strategy"]
        
        CacheStrategy["Caching<br>Strategy"] --> CachingLayers["Multi-level<br>Caching"]
    end
    
    subgraph CostOptimization["Cost Optimization"]
        ResourceRightSizing["Resource<br>Right-sizing"] --> OnDemand["On-demand<br>Instances"]
        ResourceRightSizing --> SpotInstances["Spot Instances<br>(For workers)"]
        ResourceRightSizing --> Reserved["Reserved<br>Instances"]
        
        AutoShutdown["Dev/Test<br>Auto-shutdown"] --> CostMonitoring["Cost Monitoring<br>& Alerting"]
    end
    
    CDPipeline --> AWSInfrastructure
    AWSInfrastructure --> DisasterRecovery
    AWSInfrastructure --> ScalingStrategy
    AWSInfrastructure --> CostOptimization
