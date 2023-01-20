public interface BankInterface {
    double checkBalance();
    String withdrawMoney(int amount);
    String addMoney(int amount);
    double interest(int years);
}
