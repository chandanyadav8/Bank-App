//import package BankIterface;
public class SbiUser implements BankInterface {
   private String name;
    private String accountNo;
    private double balance;
    private String password;
    private static double rateOfInterest;

    @Override
    public double checkBalance() {
        return 0;
    }

    @Override
    public String withdrawMoney(int amount) {
        return null;
    }

    @Override
    public String addMoney(int amount) {
        return null;
    }

    @Override
    public double interest(int years) {
        return 0;
    }
}
