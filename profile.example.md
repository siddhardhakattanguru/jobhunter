Candidate profile

Name: Siddhardha Kattanguru Current role: Software Engineer (BA4), Barclays Global Service Centre Private Limited, Pune, India (since July 2024) Location: Pune, India

Summary

Backend engineer with 2+ years of production AWS experience designing and operating Amazon Connect contact center infrastructure at Barclays. Externalized chat APIs for a Samsung partner integration with zero customer-data leakage. Delivered multi-region disaster recovery (30-minute RTO) across two AWS regions, and eliminated 100% of unauthorized agent-configuration incidents with an automated Lambda + Kinesis pipeline. Strong in Go and Java, event-driven design, and API gateway security, with DynamoDB, S3, CloudWatch and API Gateway.

Experience
Software Engineer (BA4), Barclays Global Service Centre, Pune - Jul 2024 to present
Externalized Barclays chat APIs to a Samsung partner integration (Vault): designed gateway-fronted external endpoints with token-based partner authentication so Samsung Vault users can reach Barclays chat from their own interface, with zero customer-data leakage.
Built a customer virtual assistant chat flow on Amazon Connect where a bot joins the contact first and resolves common queries, with bot-to-agent handover that preserves full conversation context. Deflects ~90% of chats from live agents while keeping resolution quality intact.
Eliminated 100% of unauthorized agent configuration incidents by architecting an event-driven AWS Lambda + Kinesis pipeline that auto-detected and remediated unauthorized phone-type changes in Amazon Connect in real time. Saves ~4 hours/week of manual security review; zero compliance breaches since deployment.
Implemented multi-region disaster recovery for Amazon Connect (us-east-1 + us-west-2) serving 500+ agents, achieving a 30-minute RTO and 99.9% availability SLA compliance during regional outages.
Developed Go-based Lambda functions for real-time chat routing, validation and failover logic, redirecting traffic dynamically using configuration stored in AWS Secrets Manager. Reduced routing errors by ~90% after migration.
Built and maintained Java-based REST APIs for chat server creation, request orchestration and lifecycle management, supporting high-availability workflows across multiple Amazon Connect instances.
Led the migration of chat infrastructure from Task v2 to Task v3, improving scalability and resiliency and reducing average message processing latency by 35%.
Contributed to code reviews, production incident debugging and backend architecture discussions, improving team code quality and reducing post-deployment defects.
Scripted and executed the migration of 20+ repositories from Bitbucket to GitLab, automating history, branch and pipeline migration and driving it through to production release with zero defects.
Education

Bachelor of Engineering in Computer Science and Engineering, Chaitanya Bharathi Institute of Technology, Hyderabad (2020-2024). CGPA: 8.54

Skills
Languages and fundamentals: Go, Java, Python, C++, REST APIs, data structures and algorithms
AWS: Lambda, S3, DynamoDB, CloudFormation, EC2, Amazon Connect, Service Catalog, API Gateway (also CloudWatch, Kinesis Data Streams, Secrets Manager)
Tools: IntelliJ, Postman, Git, Linux, Confluence, JIRA, Jenkins
Certifications
AWS Certified Cloud Practitioner (Amazon Web Services)
Recognition
Org-wide recognition at Barclays for world-class service: developed and deployed two modules in a single release with zero bugs during Production Validation Testing.