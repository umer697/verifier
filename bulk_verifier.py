import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from email_verifier import verify_email
from tqdm import tqdm
import os
import time
from collections import defaultdict

def verify_bulk(
    input_file: str,
    output_file: str = "verified_emails.csv",
    smtp_check: bool = False,
    max_workers: int = 5,
    chunk_size: int = 1000
) -> str:
    """Process emails with domain-based rate limiting"""
    try:
        if input_file.endswith('.csv'):
            df = pd.read_csv(input_file, header=None, names=['email'])
        else:
            with open(input_file, 'r') as f:
                emails = [line.strip() for line in f if line.strip()]
            df = pd.DataFrame(emails, columns=['email'])
    except Exception as e:
        raise ValueError(f"File read error: {str(e)}")

    # Group emails by domain for rate limiting
    domain_groups = defaultdict(list)
    for email in df['email']:
        domain = email.split('@')[1] if '@' in email else 'invalid'
        domain_groups[domain].append(email)

    results = []
    total_emails = len(df)
    
    def process_domain(domain_emails):
        """Process emails from same domain with 1-second delay"""
        domain_results = []
        for email in domain_emails:
            try:
                result = verify_email(email, smtp_check)
            except Exception as e:
                result = {
                    "email": email,
                    "score": 0,
                    "status": "invalid",
                    "reason": f"Verification error: {str(e)}",
                    "valid_syntax": False,
                    "valid_mx": False,
                    "is_disposable": True,
                    "mailbox_exists": False,
                    "is_spam_trap": False
                }
            domain_results.append(result)
            if smtp_check:
                time.sleep(1)  # Critical: 1-second delay per domain
        return domain_results

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_domain, emails): domain
            for domain, emails in domain_groups.items()
        }
        
        with tqdm(total=total_emails, desc="Verifying") as pbar:
            for future in as_completed(futures):
                domain_results = future.result()
                results.extend(domain_results)
                pbar.update(len(domain_results))

    result_df = pd.DataFrame(results)
    output_columns = [
        'email', 'score', 'status', 'reason',
        'valid_syntax', 'valid_mx', 'is_disposable',
        'mailbox_exists', 'is_spam_trap'
    ]
    result_df.to_csv(output_file, columns=output_columns, index=False)
    
    summary = {
        "total_emails": total_emails,
        "valid_count": len(result_df[result_df['status'] == 'valid']),
        "risky_count": len(result_df[result_df['status'] == 'risky']),
        "invalid_count": len(result_df[result_df['status'] == 'invalid']),
        "avg_score": round(result_df['score'].mean(), 1)
    }
    
    return output_file, summary

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Bulk email verifier')
    parser.add_argument('input_file', help='Path to input CSV or text file')
    parser.add_argument('--output', '-o', default='verified_emails.csv', 
                       help='Output file path')
    parser.add_argument('--smtp', action='store_true', 
                       help='Enable SMTP verification')
    parser.add_argument('--workers', '-w', type=int, default=5,
                       help='Number of worker threads')
    args = parser.parse_args()

    output_file, summary = verify_bulk(
        input_file=args.input_file,
        output_file=args.output,
        smtp_check=args.smtp,
        max_workers=args.workers
    )
    
    print(f"\nVerification complete. Results saved to {output_file}")
    print("Summary:")
    print(f"Total emails: {summary['total_emails']}")
    print(f"Valid: {summary['valid_count']}")
    print(f"Risky: {summary['risky_count']}")
    print(f"Invalid: {summary['invalid_count']}")
    print(f"Average score: {summary['avg_score']}")