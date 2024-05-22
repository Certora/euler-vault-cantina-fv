import "./VaultFull.spec";

// simple to run rules are imported from Vault.spec, others are left out. 
// to run the more complex rules, use Vault_complex_verified.conf
use rule conversionOfZero;
use rule conversionWeakIntegrity;
use rule conversionWeakMonotonicity;
use rule convertToAssetsWeakAdditivity;
use rule convertToCorrectness;
use rule convertToSharesWeakAdditivity;
use rule zeroDepositZeroShares;

