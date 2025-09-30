# Smithery Deployment Guide for Accounting Practice MCP

## 🚀 Quick Deployment

This MCP server is configured for easy deployment on Smithery with the included `smithery.yaml` configuration file.

### Prerequisites

- Smithery account with deployment permissions
- Repository access to this codebase
- Docker (for local testing)

### Deployment Steps

1. **Verify Configuration**
   ```bash
   # Check that all required files are present
   ls -la Dockerfile smithery.yaml requirements.txt server/main.py
   ```

2. **Deploy to Smithery**
   - Connect your repository to Smithery
   - The `smithery.yaml` file will be automatically detected
   - Smithery will build and deploy the MCP server

3. **Verify Deployment**
   ```bash
   # Run the deployment health check
   python deploy.py
   ```

## 📋 Configuration Details

### Dockerfile Configuration

The Dockerfile provides:

- **Base Image**: Python 3.11 slim for optimal size
- **Security**: Non-root user execution
- **Dependencies**: System packages and Python libraries
- **Health Check**: Built-in container health monitoring
- **Environment**: Proper Python path and MCP configuration

### smithery.yaml Configuration

The deployment configuration includes:

- **Build Type**: Dockerfile-based build
- **Runtime**: MCP server protocol
- **Resources**: 0.5 CPU, 1Gi memory, 2Gi storage
- **Health Checks**: Enabled with 30s timeout
- **Dependencies**: All required Python packages
- **Tools**: 10 MCP tools for accounting automation

### Available MCP Tools

1. `get_client_info` - Retrieve client information
2. `update_client_profile` - Update client profiles
3. `get_client_deadlines` - Get tax deadlines
4. `process_bank_statement` - Process bank statements
5. `reconcile_accounts` - Bank reconciliation
6. `calculate_tax_liability` - Tax calculations
7. `optimize_deductions` - Deduction optimization
8. `calculate_payroll` - Payroll processing
9. `sales_tax_calculation` - Sales tax calculations
10. `quickbooks_sync` - QuickBooks integration

## 🔧 Environment Variables

The following environment variables are configured:

- `PYTHONPATH`: Set to current directory
- `MCP_SERVER_NAME`: accounting-practice-mcp
- `MCP_SERVER_VERSION`: 1.0.0

## 📊 Monitoring

- **Health Check**: Available at `/health` endpoint
- **Metrics**: Request count, response time, error rate
- **Logs**: Info level with 7-day retention
- **Backup**: Daily backups with 30-day retention

## 🛠️ Troubleshooting

### Common Issues

1. **Build Failures**
   - Verify Python 3.11 compatibility
   - Check requirements.txt dependencies
   - Ensure all source files are present

2. **Runtime Errors**
   - Check health endpoint: `/health`
   - Review logs for specific error messages
   - Verify database initialization

3. **Tool Execution Issues**
   - Ensure client data is properly initialized
   - Check file permissions for data directories
   - Verify MCP client connection

### Health Check

Run the health check script to verify deployment:

```bash
python deploy.py
```

Expected output:
```
🚀 Initializing Accounting Practice MCP Server for Smithery deployment...
✅ Created directory: server/data/client_profiles
✅ Created directory: server/data/tax_tables
📊 Health Status: healthy
✅ Server is ready for deployment!
```

## 📈 Scaling

The server is configured for single replica deployment. For production scaling:

1. Update `smithery.yaml` deployment section
2. Enable auto-scaling if needed
3. Adjust resource requirements
4. Configure load balancing

## 🔒 Security

- Encryption enabled (AES-256)
- Authentication disabled by default
- Client data isolation via separate databases
- Audit logging enabled

## 📞 Support

For deployment issues:

1. Check Smithery documentation
2. Review server logs
3. Run health check script
4. Verify configuration files

---

**Ready to deploy!** 🚀

The server is fully configured and ready for Smithery deployment with comprehensive accounting automation capabilities.
