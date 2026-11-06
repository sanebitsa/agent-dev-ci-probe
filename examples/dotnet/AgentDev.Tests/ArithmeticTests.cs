using AgentDev.Sample;
using Xunit;

namespace AgentDev.Tests;

public class ArithmeticTests
{
    [Fact]
    public void AddsTwoValues() => Assert.Equal(5, Arithmetic.Add(2, 3));
}
