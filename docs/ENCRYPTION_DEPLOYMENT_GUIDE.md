# End-to-End Encryption Deployment Guide

## Overview

This guide covers deploying end-to-end encryption for chat messages in Firebase. The encryption system uses:
- **AES-256-GCM** for message encryption (authenticated encryption)
- **AWS KMS** for envelope encryption of user keys
- **Per-user encryption keys** (DEK - Data Encryption Key)
- **Feature flag** for gradual rollout

## Architecture Summary

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │ Sends message
       ▼
┌─────────────────────────┐
│  Backend (Plaintext)    │ ← Temporarily decrypts for AI
│  - SQL generation       │
│  - AI processing        │
└──────┬──────────────────┘
       │ Encrypts with user's DEK
       ▼
┌─────────────────────────┐      ┌──────────────┐
│  Firebase (Encrypted)   │◀────▶│  User's DEK  │
│  - Ciphertext only      │      │  (encrypted) │
│  - Nonce per message    │      └──────┬───────┘
└─────────────────────────┘             │
                                        ▼
                                 ┌──────────────┐
                                 │  AWS KMS     │
                                 │  Master Key  │
                                 └──────────────┘
```

## Prerequisites

### 1. AWS KMS Setup

#### Create KMS Key

1. Go to AWS Console → KMS → Customer managed keys
2. Click "Create key"
3. Configure:
   - Key type: **Symmetric**
   - Key usage: **Encrypt and decrypt**
   - Regionality: **Single-Region** (choose `us-east-1` or your region)
   - Alias: `ps-labs-agent-encryption-key`
   - Description: "Master key for encrypting user chat message DEKs"

4. Key administrators: Add your AWS IAM user/role
5. Key users: Add the IAM user/role used by your backend
6. Review and create

7. **Copy the Key ID** (looks like: `arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012`)

#### Configure IAM Permissions

Ensure your backend IAM user/role has these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowKMSEncryptDecrypt",
      "Effect": "Allow",
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:DescribeKey"
      ],
      "Resource": "arn:aws:kms:us-east-1:123456789012:key/YOUR-KEY-ID"
    }
  ]
}
```

### 2. Environment Variables

Add these to your Railway/production environment:

```bash
# Encryption Configuration
ENCRYPTION_ENABLED=false          # Start with false for testing
KMS_KEY_ID=arn:aws:kms:us-east-1:123456789012:key/YOUR-KEY-ID

# AWS Credentials (should already exist)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

## Deployment Steps

### Phase 1: Deploy with Encryption Disabled (Testing)

1. **Deploy code to production** with `ENCRYPTION_ENABLED=false`

   ```bash
   git add .
   git commit -m "feat: Add end-to-end encryption infrastructure (ENCRYPTION_ENABLED=false)"
   git push origin smarter_agents
   ```

2. **Test API endpoints** are working:

   ```bash
   # Check encryption status
   curl https://ps-labs-agent-backend-production.up.railway.app/encryption/status

   # Expected response:
   {
     "encryption_enabled": false,
     "kms_configured": false,
     "environment": "production"
   }
   ```

3. **Test existing chat functionality** - ensure nothing is broken
   - Send messages via chat interface
   - Check messages are stored correctly (plaintext)
   - Verify conversation history loads

### Phase 2: Enable Encryption (Single Test User)

1. **Set environment variable** in Railway:

   ```bash
   ENCRYPTION_ENABLED=true
   KMS_KEY_ID=arn:aws:kms:us-east-1:123456789012:key/YOUR-KEY-ID
   ```

2. **Restart the application** (Railway will auto-restart)

3. **Test encryption endpoints**:

   ```bash
   # Check encryption status
   curl https://ps-labs-agent-backend-production.up.railway.app/encryption/status

   # Expected:
   {
     "encryption_enabled": true,
     "kms_configured": true,
     "environment": "production"
   }

   # Test encryption system
   curl https://ps-labs-agent-backend-production.up.railway.app/debug/encryption-test

   # Expected:
   {
     "encryption_enabled": true,
     "tests": {
       "kms_access": "✅ PASSED",
       "encryption_roundtrip": "✅ PASSED",
       "kms_key_info": {
         "key_id": "...",
         "state": "Enabled",
         "enabled": true
       }
     },
     "overall": "✅ ALL TESTS PASSED"
   }
   ```

4. **Test with a single user** (your own account):

   a. **Initialize encryption key**:
   ```bash
   curl -X POST https://ps-labs-agent-backend-production.up.railway.app/users/YOUR_USER_ID/encryption-key/initialize
   ```

   b. **Send a test message** via chat interface

   c. **Check Firebase** - message content should be encrypted:
   ```
   {
     "role": "user",
     "content": "SGVsbG8gV29ybGQhCg==...",  ← Base64 encrypted ciphertext
     "encrypted": true,
     "nonce": "abcdef123456...",
     "encryption_version": 1,
     "algorithm": "AES-256-GCM",
     "timestamp": "..."
   }
   ```

   d. **Fetch conversation history** via API - should return decrypted messages
   ```bash
   curl https://ps-labs-agent-backend-production.up.railway.app/conversations/YOUR_USER_ID/YOUR_CONV_ID/messages
   ```

5. **Test backward compatibility**:
   - Load an old conversation with plaintext messages
   - Should still display correctly (mixed encrypted/plaintext support)

### Phase 3: Enable for All Users (Gradual Rollout)

Once single-user testing is successful:

1. **Keep `ENCRYPTION_ENABLED=true`** in production
2. **Monitor logs** for encryption errors:
   ```bash
   railway logs --deployment
   ```

3. **New users** will automatically get encryption keys on first message
4. **Existing users** will get keys when they send their next message

### Phase 4: Monitor and Optimize

1. **Check KMS usage** in AWS CloudWatch:
   - Monitor KMS API calls (Encrypt/Decrypt operations)
   - Check for errors or throttling
   - Estimate costs (KMS charges per 10,000 requests)

2. **Monitor Firebase storage**:
   - Encrypted messages are ~30% larger (Base64 + metadata)
   - Check storage usage trends

3. **Check application logs** for encryption errors:
   ```bash
   railway logs --deployment | grep -i "encryption\|kms"
   ```

4. **Performance monitoring**:
   - Message save latency (encryption adds ~5-10ms)
   - Conversation load latency (decryption overhead)

## Rollback Plan

If issues occur, you can quickly disable encryption:

1. **Set environment variable**:
   ```bash
   ENCRYPTION_ENABLED=false
   ```

2. **Restart application**

3. **Result**:
   - New messages will be stored as plaintext
   - Existing encrypted messages will still be decrypted correctly
   - System falls back to plaintext mode gracefully

## Security Considerations

### What's Protected

✅ **Messages encrypted at rest** in Firebase
✅ **Firebase admins cannot read messages** (need KMS access)
✅ **Separation of concerns** (Firebase + AWS KMS)
✅ **Authenticated encryption** (AES-GCM prevents tampering)
✅ **Unique nonce per message** (prevents replay attacks)

### What's NOT Protected

⚠️ **Backend sees plaintext** temporarily (necessary for AI processing)
⚠️ **KMS compromise** = all keys compromised
⚠️ **AWS account compromise** = can decrypt messages
⚠️ **Message metadata** not encrypted (timestamps, roles, conversation IDs)

### Best Practices

1. **Rotate KMS key annually** (AWS KMS automatic key rotation)
2. **Monitor KMS access logs** in CloudTrail
3. **Restrict KMS key access** to only backend IAM role
4. **Use separate KMS keys** for dev/staging/production
5. **Enable CloudWatch alarms** for unusual KMS usage

## Troubleshooting

### Issue: "KMS_KEY_ID must be set when ENCRYPTION_ENABLED=true"

**Solution**: Add `KMS_KEY_ID` environment variable with your KMS key ARN

### Issue: "KMS encryption failed: AccessDeniedException"

**Solution**: Check IAM permissions - backend role needs `kms:Encrypt` and `kms:Decrypt` permissions

### Issue: "Decryption failed" when loading messages

**Possible causes**:
1. KMS key was deleted/disabled
2. AWS credentials expired
3. Wrong KMS key ID in config
4. Corrupted encrypted data in Firebase

**Debug**:
```bash
# Check KMS key status
aws kms describe-key --key-id YOUR-KEY-ID

# Test KMS access
curl https://ps-labs-agent-backend-production.up.railway.app/debug/encryption-test
```

### Issue: Messages not being encrypted

**Check**:
1. Is `ENCRYPTION_ENABLED=true`?
2. Check logs: `railway logs --deployment | grep "Message encrypted"`
3. Verify Firebase documents have `"encrypted": true` field

## Testing Checklist

Before going live:

- [ ] KMS key created and accessible
- [ ] IAM permissions configured correctly
- [ ] Environment variables set in Railway
- [ ] `/encryption/status` returns `encryption_enabled: true`
- [ ] `/debug/encryption-test` shows all tests passed
- [ ] Test user can send/receive encrypted messages
- [ ] Conversation history loads correctly
- [ ] Old plaintext messages still display (backward compatibility)
- [ ] Encryption key auto-creates on first message
- [ ] Performance is acceptable (<100ms overhead per message)
- [ ] CloudWatch logs show no KMS errors

## Cost Estimation

### AWS KMS Costs

- **Key storage**: $1/month per customer managed key
- **API requests**: $0.03 per 10,000 requests
- **Estimated monthly cost** (1000 active users, 50 messages/day):
  - Key storage: $1
  - API requests: ~$4.50 (1,500,000 requests/month)
  - **Total: ~$5.50/month**

### Firebase Storage

- Encrypted messages are ~30% larger than plaintext
- If current storage is 1 GB, expect ~1.3 GB after encryption
- Firebase Blaze plan: $0.026/GB after 1 GB free tier

## Support

For issues or questions:
1. Check logs: `railway logs --deployment`
2. Test encryption: `/debug/encryption-test`
3. Review this guide
4. Contact: sagnik@photospherelabs.com

## Related Documentation

- [AWS KMS Documentation](https://docs.aws.amazon.com/kms/)
- [AES-GCM Specification](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38d.pdf)
- [Firebase Security Rules](https://firebase.google.com/docs/firestore/security/get-started)
